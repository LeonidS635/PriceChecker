from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _parse_bool(value: str) -> bool:
    return value.lower() == "true"


@dataclass(frozen=True)
class Settings:
    minio_endpoint_url: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool

    nats_url: str
    nats_consumer_stream: str
    nats_consumer_subject: str
    nats_consumer_durable: str
    nats_consumer_max_deliver: int
    nats_stream: str
    nats_subject: str

    openai_api_key: str
    openai_model: str
    openai_base_url: str | None

    gliner_device: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        return cls(
            minio_endpoint_url=os.environ["RFQ_MINIO_ENDPOINT_URL"],
            minio_access_key=os.environ["RFQ_MINIO_ACCESS_KEY"],
            minio_secret_key=os.environ["RFQ_MINIO_SECRET_KEY"],
            minio_bucket=os.environ["RFQ_MINIO_BUCKET"],
            minio_secure=_parse_bool(os.environ["RFQ_MINIO_SECURE"]),
            nats_url=os.environ["RFQ_NATS_URL"],
            nats_consumer_stream=os.environ.get("RFQ_NATS_CONSUMER_STREAM", "RFQ_EXTRACT"),
            nats_consumer_subject=os.environ.get("RFQ_NATS_CONSUMER_SUBJECT", "rfq.extract.requests"),
            nats_consumer_durable=os.environ.get("RFQ_NATS_CONSUMER_DURABLE", "rfq-extractor"),
            nats_consumer_max_deliver=int(os.environ.get("RFQ_NATS_CONSUMER_MAX_DELIVER", "5")),
            nats_stream=os.environ.get("RFQ_NATS_STREAM", "RFQ_PARTS"),
            nats_subject=os.environ.get("RFQ_NATS_SUBJECT", "rfq.parts.extracted"),
            openai_api_key=os.environ["RFQ_OPENAI_API_KEY"],
            openai_model=os.environ.get("RFQ_OPENAI_MODEL", "gpt-4o-mini"),
            openai_base_url=os.environ.get("RFQ_OPENAI_BASE_URL"),
            gliner_device=os.environ.get("RFQ_GLINER_DEVICE", "cpu"),
        )
