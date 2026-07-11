from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import msal
import requests

from listener.config import Settings
from listener.models import Attachment, EmailMessage

GRAPH_SCOPES = ["Mail.Read"]


class GraphMailClient:
    def __init__(self, settings: Settings) -> None:
        self.tenant_id = settings.graph_tenant_id
        self.client_id = settings.graph_client_id
        self._delta_link_path = Path(settings.graph_delta_link_path)
        self._token_cache_path = Path(settings.graph_token_cache_path)

    def iter_new_messages(self) -> Iterable[EmailMessage]:
        """Yield only messages that arrived since the last call using Graph delta query.

        On first run fetches all inbox messages to establish the baseline and saves a
        deltaLink.  Every subsequent run uses that deltaLink so only genuinely new
        messages are returned regardless of read/unread state.
        """
        url = self._next_delta_url()

        while url:
            response = requests.get(url, headers=self._headers(), timeout=30)
            response.raise_for_status()
            data = response.json()

            for raw in data.get("value", []):
                # Deleted/moved messages appear in delta with @removed; skip them.
                if "@removed" in raw:
                    continue
                message_id = raw["id"]
                attachments = self._load_attachments(message_id) if raw.get("hasAttachments") else []
                yield EmailMessage(
                    source_message_id=message_id,
                    internet_message_id=raw.get("internetMessageId"),
                    conversation_id=raw.get("conversationId"),
                    sender_email=raw.get("from", {}).get("emailAddress", {}).get("address", ""),
                    subject=raw.get("subject") or "",
                    received_at=self._parse_datetime(raw.get("receivedDateTime")),
                    body=raw.get("body", {}).get("content") or "",
                    body_content_type=(raw.get("body", {}).get("contentType") or "text").lower(),
                    attachments=attachments,
                )

            # Graph paginates with @odata.nextLink; when done it gives @odata.deltaLink.
            if "@odata.deltaLink" in data:
                self._save_delta_link(data["@odata.deltaLink"])
                url = None
            else:
                url = data.get("@odata.nextLink")

    def _next_delta_url(self) -> str:
        if self._delta_link_path.exists():
            saved = self._delta_link_path.read_text().strip()
            if saved:
                return saved

        # First run: $deltaToken=latest skips all existing messages and returns a
        # deltaLink anchored to "now", so only future messages will be delivered.
        return (
            f"https://graph.microsoft.com/v1.0/me"
            f"/mailFolders/inbox/messages/delta"
            f"?$deltaToken=latest"
        )

    def _save_delta_link(self, link: str) -> None:
        self._delta_link_path.parent.mkdir(parents=True, exist_ok=True)
        self._delta_link_path.write_text(link)

    def _load_attachments(self, message_id: str) -> list[Attachment]:
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
        response = requests.get(url, headers=self._headers(), timeout=30)
        response.raise_for_status()

        attachments: list[Attachment] = []
        for raw in response.json().get("value", []):
            if raw.get("@odata.type") != "#microsoft.graph.fileAttachment":
                continue
            attachments.append(
                Attachment(
                    filename=raw.get("name") or "attachment",
                    content=base64.b64decode(raw.get("contentBytes") or ""),
                    content_type=raw.get("contentType") or "application/octet-stream",
                )
            )
        return attachments

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token()}", "Content-Type": "application/json"}

    def _access_token(self) -> str:
        if not self._token_cache_path.exists():
            raise RuntimeError(
                f"Graph token cache not found at {self._token_cache_path}. "
                "Run `python connect_mailbox.py` before starting the listener."
            )

        cache = msal.SerializableTokenCache()
        cache.deserialize(self._token_cache_path.read_text())
        app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=cache,
        )

        accounts = app.get_accounts()
        if not accounts:
            raise RuntimeError(
                f"Graph token cache at {self._token_cache_path} does not contain an account. "
                "Run `python connect_mailbox.py` to connect a mailbox."
            )

        result = app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0]) or {}
        if cache.has_state_changed:
            self._token_cache_path.write_text(cache.serialize())

        if "access_token" not in result:
            error = result.get("error_description") or result.get("error") or "unknown error"
            raise RuntimeError(f"Could not acquire Graph access token from cache: {error}")

        return result["access_token"]

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
