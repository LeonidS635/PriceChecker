from __future__ import annotations

import logging
import signal
import time

from listener.config import Settings
from listener.filters.rfq import client_id_for_sender, should_process_email
from listener.mail.client import MailClient
from listener.models import EmailMessage, RfqJob, StoredObject, stable_job_id
from listener.publisher.client import Publisher
from listener.storage.client import Storage

logger = logging.getLogger(__name__)

_shutdown = False


def _request_shutdown(signum: int, _frame: object) -> None:
    global _shutdown
    logger.info("Received signal %s, shutting down", signum)
    _shutdown = True


def run(
    settings: Settings,
    mail: MailClient,
    storage: Storage,
    publisher: Publisher,
) -> None:
    signal.signal(signal.SIGINT, _request_shutdown)
    signal.signal(signal.SIGTERM, _request_shutdown)

    logger.info("Listener started, poll interval=%ss", settings.poll_interval_seconds)
    while not _shutdown:
        try:
            published = process_once(settings, mail, storage, publisher)
            if published:
                logger.info("Published %s RFQ jobs in this poll", published)
        except Exception:
            logger.exception("Poll iteration failed")

        if _shutdown:
            break

        time.sleep(settings.poll_interval_seconds)

    logger.info("Listener stopped")


def process_once(
    settings: Settings,
    mail: MailClient,
    storage: Storage,
    publisher: Publisher,
) -> int:
    published = 0
    for message in mail.iter_new_messages():
        if not should_process_email(message, settings.allowed_domains):
            logger.info("Skipping message '%s' from %s", message.subject, message.sender_email)
            continue

        client_id = client_id_for_sender(message.sender_email, settings.allowed_domains)
        assert client_id is not None
        body_object, attachment_objects = storage.store_email(client_id, message)
        publisher.publish(_build_job(message, client_id, body_object, attachment_objects))
        published += 1
        logger.info("Published RFQ job for message '%s'", message.subject)

    return published


def _build_job(
    message: EmailMessage,
    client_id: int,
    body_object: StoredObject,
    attachment_objects: list[StoredObject],
) -> RfqJob:
    return RfqJob(
        job_id=stable_job_id(message.idempotency_key),
        source_message_id=message.source_message_id,
        client_id=client_id,
        sender_email=message.sender_email,
        subject=message.subject,
        received_at=message.received_at,
        body_object=body_object,
        attachments=attachment_objects,
        metadata={
            "internet_message_id": message.internet_message_id,
            "conversation_id": message.conversation_id,
            "body_content_type": message.body_content_type,
            "idempotency_key": message.idempotency_key,
        },
    )
