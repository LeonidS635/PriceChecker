from __future__ import annotations

from typing import Protocol


class Anonymizer(Protocol):
    def anonymize(self, text: str) -> str:
        """Replace PII in the text with placeholder tokens before LLM processing."""
        ...
