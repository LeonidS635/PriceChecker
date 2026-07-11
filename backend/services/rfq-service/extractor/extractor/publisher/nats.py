from __future__ import annotations

import asyncio
import logging

import nats
import nats.js.errors

from extractor.config import Settings
from extractor.models import ExtractionResult

logger = logging.getLogger(__name__)


class NATSPublisher:
    def __init__(self, settings: Settings) -> None:
        self._url = settings.nats_url
        self._stream = settings.nats_stream
        self._subject = settings.nats_subject

    def publish(self, result: ExtractionResult) -> None:
        asyncio.run(self._publish(result))

    async def _publish(self, result: ExtractionResult) -> None:
        nc = await nats.connect(self._url)
        try:
            js = nc.jetstream()
            await self._ensure_stream(js)
            ack = await js.publish(self._subject, result.to_json().encode())
            logger.info(
                "Published job %s to NATS stream %s (seq=%s)",
                result.job_id,
                ack.stream,
                ack.seq,
            )
        finally:
            await nc.drain()

    async def _ensure_stream(self, js: nats.js.JetStreamContext) -> None:
        try:
            await js.find_stream_name_by_subject(self._subject)
        except nats.js.errors.NotFoundError:
            await js.add_stream(name=self._stream, subjects=[self._subject])
            logger.info("Created NATS JetStream stream %r", self._stream)
