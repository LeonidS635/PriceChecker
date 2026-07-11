from __future__ import annotations

import asyncio
import logging
import signal
from typing import Callable

import nats
import nats.js.api
import nats.js.errors

from extractor.config import Settings

logger = logging.getLogger(__name__)


class NATSConsumer:
    def __init__(self, settings: Settings) -> None:
        self._url = settings.nats_url
        self._stream = settings.nats_consumer_stream
        self._subject = settings.nats_consumer_subject
        self._durable = settings.nats_consumer_durable
        self._max_deliver = settings.nats_consumer_max_deliver

    def consume(self, callback: Callable[[bytes], None]) -> None:
        asyncio.run(self._consume(callback))

    async def _consume(self, callback: Callable[[bytes], None]) -> None:
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

        nc = await nats.connect(self._url)
        js = nc.jetstream()
        await self._ensure_stream(js)

        async def _handle(msg: nats.aio.client.Msg) -> None:
            try:
                await loop.run_in_executor(None, callback, msg.data)
                await msg.ack()
            except Exception:
                num_delivered = msg.metadata.num_delivered if msg.metadata else 1
                if num_delivered >= self._max_deliver:
                    logger.exception(
                        "Failed to process message after %d delivery attempt(s), giving up",
                        num_delivered,
                    )
                    await msg.term()
                else:
                    logger.exception(
                        "Failed to process message (attempt %d/%d), nacking",
                        num_delivered,
                        self._max_deliver,
                    )
                    await msg.nak()

        # max_ack_pending=1 keeps processing strictly sequential (one message
        # in flight at a time), matching the previous fully-blocking behavior.
        consumer_config = nats.js.api.ConsumerConfig(max_deliver=self._max_deliver, max_ack_pending=1)
        sub = await js.subscribe(
            self._subject,
            durable=self._durable,
            cb=_handle,
            config=consumer_config,
        )
        logger.info(
            "Subscribed to NATS subject %r (stream=%r, durable=%r)",
            self._subject,
            self._stream,
            self._durable,
        )

        try:
            await stop_event.wait()
        finally:
            await sub.unsubscribe()
            await nc.drain()
            logger.info("NATS consumer stopped")

    async def _ensure_stream(self, js: nats.js.JetStreamContext) -> None:
        try:
            await js.find_stream_name_by_subject(self._subject)
        except nats.js.errors.NotFoundError:
            await js.add_stream(name=self._stream, subjects=[self._subject])
            logger.info("Created NATS JetStream stream %r", self._stream)
