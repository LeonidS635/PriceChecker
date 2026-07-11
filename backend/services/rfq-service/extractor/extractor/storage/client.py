from __future__ import annotations

from typing import Protocol


class Storage(Protocol):
    def download(self, bucket: str, key: str) -> bytes:
        """Download an object from storage and return its raw bytes."""
        ...

    def download_if_exists(self, bucket: str, key: str) -> bytes | None:
        """Download an object, returning None if it does not exist."""
        ...

    def upload(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Upload raw bytes to storage, overwriting any existing object."""
        ...

    def delete_if_exists(self, bucket: str, key: str) -> None:
        """Delete an object from storage if it exists; no-op otherwise."""
        ...
