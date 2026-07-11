from __future__ import annotations

import io

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from extractor.config import Settings


class S3Storage:
    def __init__(self, settings: Settings) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            use_ssl=settings.minio_secure,
            config=Config(signature_version="s3v4"),
        )

    def download(self, bucket: str, key: str) -> bytes:
        buf = io.BytesIO()
        self._client.download_fileobj(bucket, key, buf)
        return buf.getvalue()

    def download_if_exists(self, bucket: str, key: str) -> bytes | None:
        try:
            return self.download(bucket, key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                return None
            raise

    def upload(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self._client.upload_fileobj(
            io.BytesIO(data),
            bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    def delete_if_exists(self, bucket: str, key: str) -> None:
        self._client.delete_object(Bucket=bucket, Key=key)
