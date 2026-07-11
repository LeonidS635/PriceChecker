from __future__ import annotations

from typing import Protocol

from listener.models import RfqJob


class Publisher(Protocol):
    def publish(self, job: RfqJob) -> None:
        ...
