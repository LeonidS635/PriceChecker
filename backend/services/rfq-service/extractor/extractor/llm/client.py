from __future__ import annotations

from typing import Protocol

from extractor.models import ExtractedPart


class LLMClient(Protocol):
    def extract(self, text: str) -> list[ExtractedPart]:
        """Extract structured part records from the given (anonymised) text."""
        ...
