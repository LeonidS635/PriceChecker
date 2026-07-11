from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_allowed_domains(value: str) -> dict[str, int]:
    allowed_domains: dict[str, int] = {}
    for item in _split_csv(value):
        domain, client_id = item.split(":", 1)
        allowed_domains[_normalize_domain(domain)] = int(client_id.strip())
    return allowed_domains


def _normalize_domain(value: str) -> str:
    return value.strip().lower().lstrip("@")


def _parse_bool(value: str) -> bool:
    return value.lower() == "true"


@dataclass(frozen=True)
class Settings:
    allowed_domains: dict[str, int]

    minio_endpoint_url: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool

    nats_url: str
    nats_stream: str
    nats_subject: str

    graph_tenant_id: str
    graph_client_id: str
    graph_delta_link_path: str
    graph_token_cache_path: str
    poll_interval_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        return cls(
            allowed_domains=_parse_allowed_domains(os.environ["RFQ_ALLOWED_DOMAINS"]),
            minio_endpoint_url=os.environ["RFQ_MINIO_ENDPOINT_URL"],
            minio_access_key=os.environ["RFQ_MINIO_ACCESS_KEY"],
            minio_secret_key=os.environ["RFQ_MINIO_SECRET_KEY"],
            minio_bucket=os.environ["RFQ_MINIO_BUCKET"],
            minio_secure=_parse_bool(os.environ["RFQ_MINIO_SECURE"]),
            nats_url=os.environ["RFQ_NATS_URL"],
            nats_stream=os.environ.get("RFQ_NATS_STREAM", "RFQ_EXTRACT"),
            nats_subject=os.environ.get("RFQ_NATS_SUBJECT", "rfq.extract.requests"),
            graph_tenant_id=os.environ["RFQ_GRAPH_TENANT_ID"],
            graph_client_id=os.environ["RFQ_GRAPH_CLIENT_ID"],
            graph_delta_link_path=os.environ["RFQ_GRAPH_DELTA_LINK_PATH"],
            graph_token_cache_path=os.environ["RFQ_GRAPH_TOKEN_CACHE_PATH"],
            poll_interval_seconds=int(os.environ["RFQ_POLL_INTERVAL_SECONDS"]),
        )

