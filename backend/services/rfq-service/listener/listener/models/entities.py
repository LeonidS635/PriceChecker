from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_job_id(source_message_id: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"rfq-listener:{source_message_id}")


def _json_default(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


@dataclass(frozen=True)
class Attachment:
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"

    @property
    def size(self) -> int:
        return len(self.content)

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.content)


@dataclass(frozen=True)
class EmailMessage:
    source_message_id: str
    sender_email: str
    subject: str
    received_at: datetime
    body: str
    body_content_type: str = "text/plain"
    internet_message_id: str | None = None
    conversation_id: str | None = None
    attachments: list[Attachment] = field(default_factory=list)

    @property
    def idempotency_key(self) -> str:
        return self.internet_message_id or self.source_message_id

    @property
    def body_bytes(self) -> bytes:
        return self.body.encode("utf-8")


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    content_type: str
    size: int
    sha256: str
    filename: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "bucket": self.bucket,
            "key": self.key,
            "content_type": self.content_type,
            "size": self.size,
            "sha256": self.sha256,
        }
        if self.filename is not None:
            payload["filename"] = self.filename
        return payload


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_message_id": self.source_message_id,
            "client_id": self.client_id,
            "sender_email": self.sender_email,
            "subject": self.subject,
            "received_at": self.received_at.isoformat(),
            "body_object": self.body_object.to_dict(),
            "attachments": [attachment.to_dict() for attachment in self.attachments],
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, default=_json_default)
