from __future__ import annotations

from typing import Iterable, Protocol

from listener.models import EmailMessage


class MailClient(Protocol):
    def iter_new_messages(self) -> Iterable[EmailMessage]:
        ...

    def has_sent_message(self, message_id: str) -> bool:
        """Return True if Message-ID exists in the configured Sent mailbox."""
        ...
