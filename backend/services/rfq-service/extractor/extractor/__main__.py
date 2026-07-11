from __future__ import annotations

import logging

from extractor.anonymizer.gliner import GLiNERAnonymizer
from extractor.config import Settings
from extractor.consumer.nats import NATSConsumer
from extractor.llm.openai import OpenAILLMClient
from extractor.pipeline import run
from extractor.publisher.nats import NATSPublisher
from extractor.storage.s3 import S3Storage

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = Settings.from_env()

    anonymizer = GLiNERAnonymizer(device=settings.gliner_device)
    anonymizer.warmup()

    run(
        consumer=NATSConsumer(settings),
        storage=S3Storage(settings),
        llm=OpenAILLMClient(settings),
        anonymizer=anonymizer,
        publisher=NATSPublisher(settings),
    )


if __name__ == "__main__":
    main()
