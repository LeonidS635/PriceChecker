from __future__ import annotations

from typing import Protocol

from listener.models import EmailMessage, StoredObject


class Storage(Protocol):
    def store_email(self, client_id: int, message: EmailMessage) -> tuple[StoredObject, list[StoredObject]]:
        ...
