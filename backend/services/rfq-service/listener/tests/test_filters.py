from datetime import datetime, timezone
from pathlib import Path

from listener.filters import (
    filter_allowed_attachments,
    is_allowed_sender,
    is_rfq_email,
    should_process_email,
)
from listener.models import Attachment, EmailMessage


def _sample_message() -> EmailMessage:
    return EmailMessage(
        source_message_id="message-1",
        sender_email="rfq@example.com",
        subject="RFQ for aircraft parts",
        received_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
        body="Dear Colleagues, please provide us quote for P/N 3504699-1.",
        attachments=[
            Attachment(
                filename="request.xlsx",
                content=b"attachment-body",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        ],
    )


def test_non_rfq_message_is_rejected() -> None:
    assert not is_rfq_email(
        "Weekly meeting notes",
        "Dear team, please find minutes from our recurring sync. No quotation is requested.",
        [],
    )


def test_subject_alone_is_enough_even_with_unrelated_body() -> None:
    assert is_rfq_email(
        "RFQ: aircraft parts needed",
        "Hi, just following up on our call yesterday. Talk soon.",
        [],
    )


def test_attachment_name_alone_is_enough_even_with_unrelated_text() -> None:
    assert is_rfq_email(
        "Hello",
        "Hi, please see the file below.",
        [Attachment(filename="RFQ_2026_parts.xlsx", content=b"data")],
    )


def test_attachment_name_ignored_for_disallowed_extension() -> None:
    assert not is_rfq_email(
        "Hello",
        "Hi, please see the file below.",
        [Attachment(filename="rfq_scan.png", content=b"data")],
    )


def test_implicit_english_price_request_without_rfq_keywords() -> None:
    assert is_rfq_email(
        "Following up",
        "Hello, we are in need of the following parts, could you please advise your best price "
        "and availability for each item? Thanks.",
        [],
    )


def test_implicit_english_aog_request() -> None:
    assert is_rfq_email(
        "Urgent",
        "AOG situation, please check availability for the attached part numbers ASAP.",
        [],
    )


def test_implicit_russian_price_request_without_direct_keywords() -> None:
    assert is_rfq_email(
        "",
        "Добрый день! Просим Вас срочно предоставить стоимость и наличие по позициям ниже.",
        [],
    )


def test_implicit_english_followup_without_price_wording() -> None:
    assert is_rfq_email(
        "",
        "The DL for this request is 02.Jun.2026.\n"
        "Please provide us with your feedback before this date.\n"
        "Thanks a lot in advance.\n"
        "Best regards, Ivanov Ivan\n"
        "Purchasing Department\n"
        "PJSC Aeroflot - Russian Airlines",
        [],
    )


def test_implicit_russian_stock_and_price_question() -> None:
    assert is_rfq_email(
        "",
        "Здравствуйте, подскажите, пожалуйста, сколько стоит деталь с номером 123-45 и есть ли она в наличии.",
        [],
    )


def test_sender_allow_list_matches_by_domain_case_insensitively() -> None:
    allowed = {"example.com": 1}

    assert is_allowed_sender("Anyone@Example.com", allowed)
    assert is_allowed_sender("someone.else@example.com", allowed)
    assert not is_allowed_sender("user@other.com", allowed)


def test_allowed_attachment_extensions_are_filtered() -> None:
    attachments = [
        Attachment(filename="request.xlsx", content=b"xlsx"),
        Attachment(filename="image.png", content=b"png"),
        Attachment(filename="quote.pdf", content=b"pdf"),
    ]

    assert [item.filename for item in filter_allowed_attachments(attachments)] == [
        "request.xlsx",
        "quote.pdf",
    ]


def test_should_process_requires_allowed_domain() -> None:
    message = _sample_message()
    allowed = {"example.com": 42}

    assert should_process_email(message, allowed)
    assert not should_process_email(message, {"other.com": 99})
