from __future__ import annotations

import os
from pathlib import Path

import msal
from dotenv import load_dotenv


GRAPH_SCOPES = ["Mail.Read"]


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _load_token_cache(path: Path) -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if path.exists():
        cache.deserialize(path.read_text())
    return cache


def main() -> None:
    load_dotenv()

    tenant_id = _required_env("RFQ_GRAPH_TENANT_ID")
    client_id = _required_env("RFQ_GRAPH_CLIENT_ID")
    token_cache_path = Path(_required_env("RFQ_GRAPH_TOKEN_CACHE_PATH"))
    token_cache_path.parent.mkdir(parents=True, exist_ok=True)

    cache = _load_token_cache(token_cache_path)
    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache,
    )

    flow = app.initiate_device_flow(scopes=GRAPH_SCOPES)
    if "user_code" not in flow:
        error = flow.get("error_description") or flow.get("error") or "unknown error"
        raise RuntimeError(f"Could not start Microsoft device flow: {error}")

    print(flow["message"], flush=True)
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        error = result.get("error_description") or result.get("error") or "unknown error"
        raise RuntimeError(f"Could not connect mailbox: {error}")

    if cache.has_state_changed:
        token_cache_path.write_text(cache.serialize())

    print(f"Mailbox connected. Token cache saved to {token_cache_path}.")


if __name__ == "__main__":
    main()
