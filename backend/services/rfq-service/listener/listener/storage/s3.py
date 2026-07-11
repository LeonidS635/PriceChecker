from __future__ import annotations

import re
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from listener.config import Settings
from listener.filters.rfq import filter_allowed_attachments
from listener.models import Attachment, EmailMessage, StoredObject, sha256_bytes


def _sanitize_key_segment(value: str) -> str:
    """Strip characters unsafe or ambiguous in S3 object key path segments."""
    value = re.sub(r'[<>"\\?\s]', "", value)
    return value or "unknown"


def _body_key(client_id: int, message: EmailMessage) -> str:
    suffix = "html" if message.body_content_type == "html" else "txt"
    msg_key = _sanitize_key_segment(message.idempotency_key)
    return f"emails/{client_id}/{msg_key}/body.{suffix}"


def _attachment_key(client_id: int, message: EmailMessage, attachment: Attachment, index: int) -> str:
    msg_key = _sanitize_key_segment(message.idempotency_key)
    suffix = Path(attachment.filename).suffix
    return f"emails/{client_id}/{msg_key}/attachments/{index:02d}{suffix}"


class S3Storage:
    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.minio_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            use_ssl=settings.minio_secure,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket()

    def store_email(self, client_id: int, message: EmailMessage) -> tuple[StoredObject, list[StoredObject]]:
        body_content_type = (
            "text/html; charset=utf-8" if message.body_content_type == "html" else "text/plain; charset=utf-8"
        )
        body_object = self._put(_body_key(client_id, message), message.body_bytes, body_content_type)
        attachment_objects = [
            self._put(
                _attachment_key(client_id, message, attachment, index),
                attachment.content,
                attachment.content_type,
                filename=attachment.filename,
            )
            for index, attachment in enumerate(filter_allowed_attachments(message.attachments), start=1)
        ]
        return body_object, attachment_objects

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self.bucket)

    def _put(
        self,
        key: str,
        data: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> StoredObject:
        digest = sha256_bytes(data)
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata={"sha256": digest},
        )
        return StoredObject(
            bucket=self.bucket,
            key=key,
            content_type=content_type,
            size=len(data),
            sha256=digest,
            filename=filename,
        )
