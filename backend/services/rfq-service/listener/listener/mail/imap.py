from __future__ import annotations

import email
import email.policy
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage as MimeMessage
from email.utils import parseaddr
from pathlib import Path
from typing import Any, Iterable

from imapclient import IMAPClient

from listener.config import Settings
from listener.models import Attachment, EmailMessage

logger = logging.getLogger(__name__)

FETCH_BATCH_SIZE = 20


@dataclass(frozen=True)
class FolderCursor:
    uidvalidity: int
    last_uid: int


def _load_state(path: Path) -> dict[str, dict[str, int]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        return {}
    return data


def _save_state(path: Path, state: dict[str, dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def _folder_cursor(state: dict[str, dict[str, int]], mailbox: str) -> FolderCursor | None:
    raw = state.get(mailbox)
    if not raw:
        return None
    return FolderCursor(uidvalidity=int(raw["uidvalidity"]), last_uid=int(raw["last_uid"]))


def _set_folder_cursor(
    state: dict[str, dict[str, int]],
    mailbox: str,
    cursor: FolderCursor,
) -> None:
    state[mailbox] = {
        "uidvalidity": cursor.uidvalidity,
        "last_uid": cursor.last_uid,
    }


def _normalize_internal_date(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _extract_body(msg: MimeMessage) -> tuple[str, str]:
    html_parts: list[str] = []
    plain_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            if content_type == "text/html":
                html_parts.append(part.get_content())
            elif content_type == "text/plain":
                plain_parts.append(part.get_content())
    else:
        content_type = msg.get_content_type()
        payload = msg.get_content()
        if content_type == "text/html":
            html_parts.append(payload)
        else:
            plain_parts.append(payload)

    if html_parts:
        return "\n".join(html_parts), "html"
    if plain_parts:
        return "\n".join(plain_parts), "text"
    return "", "text"


def _extract_attachments(msg: MimeMessage) -> list[Attachment]:
    attachments: list[Attachment] = []
    for part in msg.iter_attachments():
        filename = part.get_filename() or "attachment"
        content = part.get_payload(decode=True) or b""
        attachments.append(
            Attachment(
                filename=filename,
                content=content,
                content_type=part.get_content_type() or "application/octet-stream",
            )
        )
    return attachments


def _parse_raw_message(
    mailbox: str,
    uid: int,
    raw_message: bytes,
    internal_date: datetime,
) -> EmailMessage:
    msg = email.message_from_bytes(raw_message, policy=email.policy.default)
    body, body_content_type = _extract_body(msg)
    sender_email = parseaddr(msg.get("From", ""))[1]

    return EmailMessage(
        source_message_id=f"{mailbox}:uid-{uid}",
        internet_message_id=msg.get("Message-Id"),
        conversation_id=None,
        in_reply_to=msg.get("In-Reply-To"),
        references=msg.get("References"),
        sender_email=sender_email,
        subject=msg.get("Subject", "") or "",
        received_at=_normalize_internal_date(internal_date),
        body=body,
        body_content_type=body_content_type,
        attachments=_extract_attachments(msg),
    )


class ImapMailClient:
    def __init__(self, settings: Settings) -> None:
        self._host = settings.imap_host
        self._port = settings.imap_port
        self._use_ssl = settings.imap_use_ssl
        self._username = settings.imap_username
        self._password = settings.imap_password
        self._mailboxes = settings.imap_mailboxes
        self._state_path = Path(settings.imap_state_path)

    def iter_new_messages(self) -> Iterable[EmailMessage]:
        state = _load_state(self._state_path)

        with IMAPClient(self._host, port=self._port, ssl=self._use_ssl) as client:
            client.login(self._username, self._password)
            logger.debug("Connected to IMAP %s as %s", self._host, self._username)

            for mailbox in self._mailboxes:
                yield from self._iter_folder_messages(client, mailbox, state)

        _save_state(self._state_path, state)

    def _iter_folder_messages(
        self,
        client: IMAPClient,
        mailbox: str,
        state: dict[str, dict[str, int]],
    ) -> Iterable[EmailMessage]:
        try:
            folder_info = client.select_folder(mailbox, readonly=False)
        except Exception:
            logger.exception("Failed to select IMAP folder '%s'", mailbox)
            return

        uidvalidity = int(folder_info[b"UIDVALIDITY"])
        cursor = _folder_cursor(state, mailbox)

        if cursor is None or cursor.uidvalidity != uidvalidity:
            uidnext = int(folder_info.get(b"UIDNEXT", 1))
            baseline = FolderCursor(uidvalidity=uidvalidity, last_uid=max(uidnext - 1, 0))
            _set_folder_cursor(state, mailbox, baseline)
            _save_state(self._state_path, state)
            logger.info(
                "Initialized IMAP cursor for folder '%s' at UID %s (uidvalidity=%s)",
                mailbox,
                baseline.last_uid,
                uidvalidity,
            )
            return

        found = client.search(["UID", f"{cursor.last_uid + 1}:*"])
        uids = sorted(uid for uid in found if uid > cursor.last_uid)

        logger.info("Folder '%s': %d new message(s) since UID %d", mailbox, len(uids), cursor.last_uid)
        
        if not uids:
            return

        for batch_start in range(0, len(uids), FETCH_BATCH_SIZE):
            batch = uids[batch_start : batch_start + FETCH_BATCH_SIZE]
            fetched = client.fetch(batch, ["BODY.PEEK[]", "INTERNALDATE"])

            for uid in batch:
                raw_data = fetched[uid]
                raw_message = raw_data[b"BODY[]"]
                internal_date = raw_data[b"INTERNALDATE"]
                message = _parse_raw_message(mailbox, uid, raw_message, internal_date)
                yield message

                updated = FolderCursor(uidvalidity=uidvalidity, last_uid=uid)
                _set_folder_cursor(state, mailbox, updated)
                _save_state(self._state_path, state)
