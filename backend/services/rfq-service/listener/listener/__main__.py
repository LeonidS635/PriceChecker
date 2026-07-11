from __future__ import annotations

import logging

from listener.config import Settings
from listener.mail.graph import GraphMailClient
from listener.pipeline import run
from listener.publisher.nats import NATSPublisher
from listener.storage.s3 import S3Storage

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = Settings.from_env()
    run(
        settings,
        GraphMailClient(settings),
        S3Storage(settings),
        NATSPublisher(settings),
    )


if __name__ == "__main__":
    main()
