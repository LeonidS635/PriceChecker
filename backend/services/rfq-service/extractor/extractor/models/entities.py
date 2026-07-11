from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    content_type: str
    size: int
    sha256: str
    filename: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StoredObject":
        return cls(
            bucket=d["bucket"],
            key=d["key"],
            content_type=d["content_type"],
            size=d["size"],
            sha256=d["sha256"],
            filename=d.get("filename"),
        )


def _json_default(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def _parse_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


@dataclass(frozen=True)
class RfqJob:
    job_id: UUID
    source_message_id: str
    client_id: int
    sender_email: str
    subject: str
    received_at: datetime
    body_object: StoredObject
    attachments: list[StoredObject]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RfqJob":
        received_at_raw = d["received_at"]
        if isinstance(received_at_raw, str):
            received_at = datetime.fromisoformat(received_at_raw)
        else:
            received_at = datetime.now(timezone.utc)

        return cls(
            job_id=_parse_uuid(d["job_id"]),
            source_message_id=d["source_message_id"],
            client_id=int(d["client_id"]),
            sender_email=d["sender_email"],
            subject=d.get("subject", ""),
            received_at=received_at,
            body_object=StoredObject.from_dict(d["body_object"]),
            attachments=[StoredObject.from_dict(a) for a in d.get("attachments", [])],
            metadata=d.get("metadata", {}),
        )


@dataclass(frozen=True)
class ExtractedPart:
    part_number: str
    description: str | None = None
    quantity: int | None = None
    alternatives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "part_number": self.part_number,
            "description": self.description,
            "quantity": self.quantity,
            "alternatives": self.alternatives,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ExtractedPart":
        return cls(
            part_number=d["part_number"],
            description=d.get("description"),
            quantity=d.get("quantity"),
            alternatives=list(d.get("alternatives", [])),
        )


@dataclass(frozen=True)
class ExtractionResult:
    job_id: UUID
    source_message_id: str
    client_id: int
    sender_email: str
    subject: str
    received_at: datetime
    parts: list[ExtractedPart]
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1",
            "job_id": self.job_id,
            "source_message_id": self.source_message_id,
            "client_id": self.client_id,
            "sender_email": self.sender_email,
            "subject": self.subject,
            "received_at": self.received_at.isoformat(),
            "processed_at": self.processed_at.isoformat(),
            "parts": [p.to_dict() for p in self.parts],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, default=_json_default)
