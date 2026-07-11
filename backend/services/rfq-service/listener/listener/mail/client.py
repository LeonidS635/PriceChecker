from __future__ import annotations

from typing import Iterable, Protocol

from listener.models import EmailMessage


class MailClient(Protocol):
    def iter_new_messages(self) -> Iterable[EmailMessage]:
        ...
