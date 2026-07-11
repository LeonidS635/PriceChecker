from __future__ import annotations

from typing import Protocol

from extractor.models import ExtractionResult


class Publisher(Protocol):
    def publish(self, result: ExtractionResult) -> None:
        """Publish an extraction result to the downstream broker."""
        ...
