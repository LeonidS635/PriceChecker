from __future__ import annotations

import logging

import tenacity
from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    LengthFinishReasonError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel, Field

from extractor.config import Settings
from extractor.models import ExtractedPart

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an aviation parts procurement assistant. Extract all requested parts from the supplied RFQ text.

For each part provide:
- part_number (required) — the part number / NSN / PN as written
- description — brief part description, or null
- quantity — requested quantity as a number (e.g. 2), or null if not specified or not parseable as a number
- alternatives — alternative part numbers mentioned by the customer, or an empty list

If no parts are found return an empty list.\
"""


class _ExtractedPartSchema(BaseModel):
    part_number: str
    description: str | None = None
    quantity: int | None = None
    alternatives: list[str] = Field(default_factory=list)


class _ExtractionSchema(BaseModel):
    parts: list[_ExtractedPartSchema] = Field(default_factory=list)


class OpenAILLMClient:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.openai_model
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(
            (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)
        ),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=60),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def extract(self, text: str) -> list[ExtractedPart]:
        try:
            completion = self._client.chat.completions.parse(
                model=self._model,
                response_format=_ExtractionSchema,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                timeout=60,
            )
        except LengthFinishReasonError:
            logger.error("LLM response was truncated before completing the schema")
            return []

        message = completion.choices[0].message
        if message.refusal:
            logger.error("LLM refused the request: %.200s", message.refusal)
            return []

        parsed = message.parsed
        if parsed is None:
            logger.error("LLM response failed schema validation")
            return []

        return _to_extracted_parts(parsed)


def _to_extracted_parts(parsed: _ExtractionSchema) -> list[ExtractedPart]:
    result: list[ExtractedPart] = []
    for item in parsed.parts:
        part_number = item.part_number.strip()
        if not part_number:
            continue
        result.append(
            ExtractedPart(
                part_number=part_number,
                description=item.description or None,
                quantity=item.quantity,
                alternatives=[a for a in item.alternatives if a],
            )
        )
    return result
