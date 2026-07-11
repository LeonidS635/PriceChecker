from __future__ import annotations

from typing import Callable, Protocol


class Consumer(Protocol):
    def consume(self, callback: Callable[[bytes], None]) -> None:
        """Block and call callback for each delivered message body.

        The implementation is responsible for acking the message after the
        callback returns without raising and nacking (requeue=False) when
        the callback raises.
        """
        ...
