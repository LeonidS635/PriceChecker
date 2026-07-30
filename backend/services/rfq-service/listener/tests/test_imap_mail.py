from __future__ import annotations

import json
from datetime import datetime, timezone
from email.message import EmailMessage as MimeEmail
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from listener.config import Settings
from listener.mail.imap import (
    FolderCursor,
    ImapMailClient,
    _extract_attachments,
    _extract_body,
    _folder_cursor,
    _load_state,
    _parse_raw_message,
    _set_folder_cursor,
)


def _settings(state_path: Path, mailboxes: list[str] | None = None) -> Settings:
    return Settings(
        allowed_domains={"example.com": 1},
        minio_endpoint_url="http://minio:9000",
        minio_access_key="minioadmin",
        minio_secret_key="minioadmin",
        minio_bucket="rfq-emails",
        minio_secure=False,
        nats_url="nats://nats:4222",
        nats_stream="RFQ_EXTRACT",
        nats_subject="rfq.extract.requests",
        imap_host="imap.test",
        imap_port=993,
        imap_use_ssl=True,
        imap_username="user@example.com",
        imap_password="secret",
        imap_mailboxes=mailboxes or ["INBOX"],
        imap_state_path=str(state_path),
        poll_interval_seconds=60,
    )


def _build_raw_message(
    *,
    subject: str = "RFQ for parts",
    body: str = "Please provide quote",
    html: str | None = None,
    with_attachment: bool = False,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> bytes:
    root = MimeEmail()
    root["From"] = "Buyer <buyer@example.com>"
    root["Subject"] = subject
    root["Message-Id"] = "<msg-123@example.com>"
    if in_reply_to is not None:
        root["In-Reply-To"] = in_reply_to
    if references is not None:
        root["References"] = references

    if html is None and not with_attachment:
        root.set_content(body)
        return root.as_bytes()

    if html is None:
        root.set_content(body)
    else:
        root.set_content(body)
        root.add_alternative(html, subtype="html")

    if with_attachment:
        root.add_attachment(
            b"excel-data",
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="request.xlsx",
        )

    return root.as_bytes()


def test_extract_body_prefers_html() -> None:
    msg = MimeEmail()
    msg.set_content("plain fallback")
    msg.add_alternative("<p>html body</p>", subtype="html")

    body, content_type = _extract_body(msg)

    assert content_type == "html"
    assert "html body" in body


def test_extract_attachments_reads_filename_and_content() -> None:
    raw = _build_raw_message(with_attachment=True)
    msg = MimeEmail()
    msg = __import__("email").message_from_bytes(raw, policy=__import__("email").policy.default)

    attachments = _extract_attachments(msg)

    assert len(attachments) == 1
    assert attachments[0].filename == "request.xlsx"
    assert attachments[0].content == b"excel-data"


def test_parse_raw_message_maps_fields() -> None:
    raw = _build_raw_message(
        in_reply_to="<parent@example.com>",
        references="<root@example.com> <parent@example.com>",
    )
    received_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    message = _parse_raw_message("INBOX", 42, raw, received_at)

    assert message.source_message_id == "INBOX:uid-42"
    assert message.internet_message_id == "<msg-123@example.com>"
    assert message.sender_email == "buyer@example.com"
    assert message.subject == "RFQ for parts"
    assert message.received_at == received_at
    assert "Please provide quote" in message.body
    assert message.in_reply_to == "<parent@example.com>"
    assert message.references == "<root@example.com> <parent@example.com>"
    assert message.is_reply


def test_folder_cursor_roundtrip_in_state() -> None:
    state: dict[str, dict[str, int]] = {}
    cursor = FolderCursor(uidvalidity=100, last_uid=55)

    _set_folder_cursor(state, "INBOX", cursor)

    loaded = _folder_cursor(state, "INBOX")
    assert loaded == cursor
    assert _folder_cursor(state, "Other") is None


def test_load_state_returns_empty_dict_for_missing_file(tmp_path: Path) -> None:
    assert _load_state(tmp_path / "missing.json") == {}


def test_load_state_reads_json_file(tmp_path: Path) -> None:
    state_path = tmp_path / "imap_state.json"
    state_path.write_text('{"INBOX": {"uidvalidity": 1, "last_uid": 9}}')

    assert _load_state(state_path) == {"INBOX": {"uidvalidity": 1, "last_uid": 9}}


class _FakeImapClient:
    def __init__(self, folders: dict[str, dict]) -> None:
        self.folders = folders
        self.current_mailbox: str | None = None

    def __enter__(self) -> "_FakeImapClient":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def login(self, _username: str, _password: str) -> None:
        return None

    def select_folder(self, mailbox: str, readonly: bool = False) -> dict[bytes, int]:
        self.current_mailbox = mailbox
        return self.folders[mailbox]["select"]

    def search(self, criteria: list[str | int]) -> list[int]:
        mailbox = self.current_mailbox
        assert mailbox is not None
        return list(self.folders[mailbox]["search"].get(tuple(criteria), []))

    def fetch(self, uids: list[int], _parts: list[str]) -> dict[int, dict[bytes, object]]:
        mailbox = self.current_mailbox
        assert mailbox is not None
        return {uid: self.folders[mailbox]["messages"][uid] for uid in uids}


@patch("listener.mail.imap.IMAPClient")
def test_first_run_initializes_cursor_without_backlog(mock_imap_class: MagicMock, tmp_path: Path) -> None:
    state_path = tmp_path / "imap_state.json"
    raw = _build_raw_message()
    received_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    fake_client = _FakeImapClient(
        {
            "INBOX": {
                "select": {b"UIDVALIDITY": 10, b"UIDNEXT": 100},
                "search": {},
                "messages": {
                    99: {b"BODY[]": raw, b"INTERNALDATE": received_at},
                },
            }
        }
    )
    mock_imap_class.return_value = fake_client

    client = ImapMailClient(_settings(state_path))
    messages = list(client.iter_new_messages())

    assert messages == []
    saved = json.loads(state_path.read_text())
    assert saved == {"INBOX": {"uidvalidity": 10, "last_uid": 99}}


@patch("listener.mail.imap.IMAPClient")
def test_subsequent_run_returns_only_new_uids(mock_imap_class: MagicMock, tmp_path: Path) -> None:
    state_path = tmp_path / "imap_state.json"
    state_path.write_text(json.dumps({"INBOX": {"uidvalidity": 10, "last_uid": 100}}))

    raw_old = _build_raw_message(subject="old")
    raw_new = _build_raw_message(subject="new")
    received_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    fake_client = _FakeImapClient(
        {
            "INBOX": {
                "select": {b"UIDVALIDITY": 10, b"UIDNEXT": 103},
                "search": {
                    ("UID", "101:*"): [101, 102],
                },
                "messages": {
                    100: {b"BODY[]": raw_old, b"INTERNALDATE": received_at},
                    101: {b"BODY[]": raw_new, b"INTERNALDATE": received_at},
                    102: {b"BODY[]": raw_new, b"INTERNALDATE": received_at},
                },
            }
        }
    )
    mock_imap_class.return_value = fake_client

    client = ImapMailClient(_settings(state_path))
    messages = list(client.iter_new_messages())

    assert [message.subject for message in messages] == ["new", "new"]
    assert json.loads(state_path.read_text())["INBOX"]["last_uid"] == 102


@patch("listener.mail.imap.IMAPClient")
def test_no_reprocessing_when_search_returns_last_uid(mock_imap_class: MagicMock, tmp_path: Path) -> None:
    # IMAP "N:*" quirk: with no new messages the server returns the highest
    # (already-processed) UID. The client must not yield or re-advance on it.
    state_path = tmp_path / "imap_state.json"
    state_path.write_text(json.dumps({"INBOX": {"uidvalidity": 10, "last_uid": 100}}))

    raw = _build_raw_message(subject="already-seen")
    received_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    fake_client = _FakeImapClient(
        {
            "INBOX": {
                "select": {b"UIDVALIDITY": 10, b"UIDNEXT": 101},
                "search": {("UID", "101:*"): [100]},
                "messages": {100: {b"BODY[]": raw, b"INTERNALDATE": received_at}},
            }
        }
    )
    mock_imap_class.return_value = fake_client

    client = ImapMailClient(_settings(state_path))
    messages = list(client.iter_new_messages())

    assert messages == []
    assert json.loads(state_path.read_text())["INBOX"]["last_uid"] == 100


@patch("listener.mail.imap.IMAPClient")
def test_uidvalidity_reset_only_rebaselines_changed_folder(mock_imap_class: MagicMock, tmp_path: Path) -> None:
    state_path = tmp_path / "imap_state.json"
    state_path.write_text(
        json.dumps(
            {
                "INBOX": {"uidvalidity": 10, "last_uid": 5},
                "Domain-A": {"uidvalidity": 20, "last_uid": 7},
            }
        )
    )

    raw = _build_raw_message(subject="fresh")
    received_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    fake_client = _FakeImapClient(
        {
            "INBOX": {
                "select": {b"UIDVALIDITY": 10, b"UIDNEXT": 8},
                "search": {("UID", "6:*"): [6]},
                "messages": {6: {b"BODY[]": raw, b"INTERNALDATE": received_at}},
            },
            "Domain-A": {
                "select": {b"UIDVALIDITY": 99, b"UIDNEXT": 50},
                "search": {},
                "messages": {},
            },
        }
    )
    mock_imap_class.return_value = fake_client

    client = ImapMailClient(_settings(state_path, mailboxes=["INBOX", "Domain-A"]))
    messages = list(client.iter_new_messages())

    assert len(messages) == 1
    assert messages[0].subject == "fresh"
    saved = json.loads(state_path.read_text())
    assert saved["INBOX"]["last_uid"] == 6
    assert saved["Domain-A"] == {"uidvalidity": 99, "last_uid": 49}


@patch("listener.mail.imap.IMAPClient")
def test_multiple_folders_are_polled_in_one_iteration(mock_imap_class: MagicMock, tmp_path: Path) -> None:
    state_path = tmp_path / "imap_state.json"
    state_path.write_text(
        json.dumps(
            {
                "INBOX": {"uidvalidity": 1, "last_uid": 1},
                "Domain-A": {"uidvalidity": 2, "last_uid": 2},
            }
        )
    )

    raw_inbox = _build_raw_message(subject="inbox-message")
    raw_domain = _build_raw_message(subject="domain-message")
    received_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    fake_client = _FakeImapClient(
        {
            "INBOX": {
                "select": {b"UIDVALIDITY": 1, b"UIDNEXT": 3},
                "search": {("UID", "2:*"): [2]},
                "messages": {2: {b"BODY[]": raw_inbox, b"INTERNALDATE": received_at}},
            },
            "Domain-A": {
                "select": {b"UIDVALIDITY": 2, b"UIDNEXT": 4},
                "search": {("UID", "3:*"): [3]},
                "messages": {3: {b"BODY[]": raw_domain, b"INTERNALDATE": received_at}},
            },
        }
    )
    mock_imap_class.return_value = fake_client

    client = ImapMailClient(_settings(state_path, mailboxes=["INBOX", "Domain-A"]))
    messages = list(client.iter_new_messages())

    assert [message.subject for message in messages] == ["inbox-message", "domain-message"]


@patch("listener.mail.imap.IMAPClient")
def test_cursor_not_advanced_when_consumer_raises(mock_imap_class: MagicMock, tmp_path: Path) -> None:
    state_path = tmp_path / "imap_state.json"
    state_path.write_text(json.dumps({"INBOX": {"uidvalidity": 10, "last_uid": 100}}))

    raw = _build_raw_message(subject="will-fail")
    received_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    fake_client = _FakeImapClient(
        {
            "INBOX": {
                "select": {b"UIDVALIDITY": 10, b"UIDNEXT": 103},
                "search": {("UID", "101:*"): [101]},
                "messages": {101: {b"BODY[]": raw, b"INTERNALDATE": received_at}},
            }
        }
    )
    mock_imap_class.return_value = fake_client

    client = ImapMailClient(_settings(state_path))

    with pytest.raises(RuntimeError, match="publish failed"):
        for message in client.iter_new_messages():
            assert message.subject == "will-fail"
            raise RuntimeError("publish failed")

    assert json.loads(state_path.read_text())["INBOX"]["last_uid"] == 100
