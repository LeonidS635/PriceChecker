from __future__ import annotations

import json
import logging

from extractor.anonymizer.client import Anonymizer
from extractor.consumer.client import Consumer
from extractor.converters.text import to_text
from extractor.llm.client import LLMClient
from extractor.models import ExtractedPart, ExtractionResult, RfqJob
from extractor.publisher.client import Publisher
from extractor.storage.client import Storage

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "_extraction_cache"


def run(
    consumer: Consumer,
    storage: Storage,
    llm: LLMClient,
    anonymizer: Anonymizer,
    publisher: Publisher,
) -> None:
    """Start the blocking consumer loop. Returns only on keyboard interrupt."""

    def handle(body: bytes) -> None:
        _process_message(body, storage, llm, anonymizer, publisher)

    consumer.consume(handle)


def _process_message(
    body: bytes,
    storage: Storage,
    llm: LLMClient,
    anonymizer: Anonymizer,
    publisher: Publisher,
) -> None:
    job = _deserialize(body)
    logger.info("Processing job %s", job.job_id)

    cache_bucket = job.body_object.bucket
    cache_key = f"{_CACHE_PREFIX}/{job.job_id}.json"

    parts = _load_cached_parts(storage, cache_bucket, cache_key)
    if parts is not None:
        logger.info(
            "Job %s: reusing cached extraction (%d part(s)), skipping LLM call",
            job.job_id,
            len(parts),
        )
    else:
        texts = _collect_texts(job, storage)
        if not texts:
            logger.error("Job %s: no extractable text found", job.job_id)
            return

        combined = "\n\n---\n\n".join(texts)
        anonymized = anonymizer.anonymize(combined)

        parts = llm.extract(anonymized) if anonymized.strip() else []
        logger.info("Job %s: extracted %d part(s)", job.job_id, len(parts))

        if len(parts) == 0:
            logger.error("Job %s: no parts extracted", job.job_id)
            return

        _store_cached_parts(storage, cache_bucket, cache_key, parts)

    logger.info("Job %s: parts: %s", job.job_id, parts)

    result = ExtractionResult(
        job_id=job.job_id,
        source_message_id=job.source_message_id,
        client_id=job.client_id,
        sender_email=job.sender_email,
        subject=job.subject,
        received_at=job.received_at,
        parts=parts,
    )
    publisher.publish(result)
    logger.info("Job %s: published result", job.job_id)

    storage.delete_if_exists(cache_bucket, cache_key)


def _load_cached_parts(storage: Storage, bucket: str, key: str) -> list[ExtractedPart] | None:
    try:
        raw = storage.download_if_exists(bucket, key)
    except Exception:
        logger.warning("Failed to check extraction cache at %s/%s, re-extracting", bucket, key, exc_info=True)
        return None

    if raw is None:
        return None

    try:
        data = json.loads(raw)
        return [ExtractedPart.from_dict(item) for item in data]
    except Exception:
        logger.warning("Failed to parse cached extraction at %s/%s, re-extracting", bucket, key, exc_info=True)
        return None


def _store_cached_parts(storage: Storage, bucket: str, key: str, parts: list[ExtractedPart]) -> None:
    payload = json.dumps([p.to_dict() for p in parts]).encode()
    try:
        storage.upload(bucket, key, payload, content_type="application/json")
    except Exception:
        logger.warning("Failed to cache extraction result at %s/%s", bucket, key, exc_info=True)


def _deserialize(body: bytes) -> RfqJob:
    try:
        data = json.loads(body)
        return RfqJob.from_dict(data)
    except Exception as exc:
        raise ValueError(f"Cannot deserialize RfqJob: {exc}") from exc


def _collect_texts(job: RfqJob, storage: Storage) -> list[str]:
    texts: list[str] = []

    body_bytes = storage.download(job.body_object.bucket, job.body_object.key)
    body_content_type = job.metadata.get("body_content_type", job.body_object.content_type)
    body_text = to_text(body_bytes, body_content_type, job.body_object.filename)
    if body_text and body_text.strip():
        texts.append(body_text)

    for obj in job.attachments:
        try:
            data = storage.download(obj.bucket, obj.key)
        except Exception:
            logger.exception("Failed to download attachment %s/%s, skipping", obj.bucket, obj.key)
            continue

        text = to_text(data, obj.content_type, obj.filename)
        if text and text.strip():
            texts.append(text)

    return texts
