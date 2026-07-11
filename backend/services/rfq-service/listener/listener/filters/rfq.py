from __future__ import annotations

import re
from pathlib import Path

from listener.models import Attachment, EmailMessage

import logging
logger = logging.getLogger(__name__)

ALLOWED_ATTACHMENT_SUFFIXES = {".txt", ".html", ".doc", ".docx", ".xlsx", ".xlsm", ".xls", ".pdf"}

# ---------------------------------------------------------------------------
# Aircraft-parts RFQ detection
#
# Subject, body and attachment names are matched independently by three
# dedicated regexes; a hit in *any one* of them is enough to classify the
# email as an RFQ (see `is_rfq_email`). Senders are already restricted to a
# known allow-list before this filter runs, so a slightly wider net here is
# preferable to missing a real RFQ: a false negative silently drops a client
# request, while a false positive only costs one extra pipeline run.
#
# The body regex is the most permissive because buyers in this domain often
# skip explicit "quote"/"request" wording entirely and just describe what
# they need (e.g. "please advise price and availability", "просим сообщить
# стоимость"). It is split into two tiers:
#   - "direct" terms: unambiguous RFQ/quotation vocabulary;
#   - "implicit" terms: price/availability/offer phrasing and aviation
#     procurement jargon (AOG, "parts required", "стоимость и наличие", ...)
#     that reliably signals a purchase inquiry even without those words.
# Subject and attachment-name regexes stay intentionally short: subjects and
# filenames are terse by nature, so only the direct vocabulary is reused
# there, plus a handful of short domain-specific tokens.
# ---------------------------------------------------------------------------

_BODY_DIRECT_EN = (
    r"\brfq\b",
    r"\brfp\b",
    r"\brequest(?:ed|ing)?\s+for\s+(?:quotation|quote|proposal)s?\b",
    r"\bquotation\s+requests?\b",
    r"\bquote\s+requests?\b",
    r"\bprice\s+requests?\b",
    r"\bpricing\s+requests?\b",
    r"\b(?:purchase|sourcing|procurement)\s+(?:inquiry|inquiries|request)\b",
    r"\b(?:material|materials|parts?|spares?)\s+(?:inquiry|inquiries)\b",
    r"\brequest\s+template\b",
    r"\battached\s+(?:rfq|request)\b",
    r"\bplease\s+find\s+attached\s+(?:the\s+)?(?:parts?|spares?)\s+list\b",
    r"\b(?:please\s+)?(?:provide|send)\s+us\s+(?:your\s+)?(?:quote|quotation)\b",
    r"\bapplication\b.{0,200}?\bquotations?\b",
    r"\btender\b",
    r"\binvitation\s+to\s+bid\b",
    r"\bbid\s+request\b",
)

_BODY_IMPLICIT_EN = (
    # "please/kindly/could you (please) send|provide|advise|confirm|quote ... price|quote|cost|offer"
    r"\b(?:(?:please|kindly|could|would|can)\s+(?:you\s+)?)*"
    r"(?:send|provide|share|forward|advise|confirm|give|quote|issue|submit)\b"
    r"[^\n.,;]{0,40}?"
    r"\b(?:quote|quotation|quotations|price|prices|pricing|cost|costs|rate|rates|proposal|proposals|offer|offers)\b",
    r"\b(?:quote|quotation|price|pricing|cost|rate|offer|proposal)s?\s+(?:for|per|on)\b",
    r"\bbest\s+(?:price|offer|quote|quotation|rate|cost)\b",
    r"\b(?:price|pricing|cost|quote|quotation)\s+(?:and|&)\s+(?:availability|lead\s*time|delivery)\b",
    r"\bavailability\s+(?:and|&)\s+(?:price|pricing|cost|quote|quotation)\b",
    r"\b(?:fob|cif|exw)\s+price\b",
    r"\bunit\s+price\b",
    r"\baog\b",
    r"\baircraft\s+on\s+ground\b",
    r"\bin\s+need\s+of\s+(?:the\s+)?(?:following\s+)?(?:parts?|spares?)\b",
    r"\blooking\s+for\s+(?:the\s+)?(?:following\s+)?(?:parts?|spares?)\b",
    r"\brequirement\s+(?:for|of)\s+(?:the\s+)?(?:following\s+)?(?:parts?|spares?)\b",
    r"\b(?:parts?|spares?)\s+(?:required|needed)\b",
    r"\bstock\s+(?:check|availability)\b",
    r"\bcheck\s+(?:the\s+)?availability\b",
    r"\bcan\s+you\s+supply\b",
    r"\bplease\s+advise\s+(?:on\s+)?availability\b",
    r"\bpurchasing\s+department\b",
    r"\bprocurement\s+department\b",
    r"\bdl\s+(?:for|of|is)\s+(?:this|the)\s+request\b",
    r"\bdeadline\s+(?:for|of)\s+(?:this|the)\s+request\b",
    r"\bprovide\s+us\s+with\s+your\s+feedback\b",
)

_BODY_DIRECT_RU = (
    r"\bзапрос(?:е|а|ом|у)?\s+(?:на\s+)?"
    r"(?:предложен(?:ий|ия|ие)|котировк[а-я]*|цен[а-я]*|стоимост[а-я]*|расценк[а-я]*)\b",
    r"\bзаявк(?:а|и|у|ой|ах|ам)?\b",
    r"\bкоммерческ(?:ое|ого|ому|им|их|ие|ая|ую)?\s+предложен(?:ие|ия|ий|ию|иях|иями)\b",
    r"\bкотировк(?:а|и|у|ой|ам|ах)?\b",
    r"\bприслать\s+предложени[а-я]*\b",
    r"\bнаправить\s+предложени[а-я]*\b",
    r"\bшаблон\s+запроса\b",
    r"\bпрайс(?:[- ]?лист)?[а-я]*\b",
    r"\bтендер[а-я]*\b",
)

_BODY_IMPLICIT_RU = (
    # "прошу/просим (вас) (срочно) предоставить|направить|прислать|сообщить ... цену|стоимость|предложение"
    r"\b(?:прошу|просим)\s+(?:вас\s+)?(?:срочно\s+)?"
    r"(?:предоставить|направить|прислать|выслать|сообщить|выставить)\b"
    r"[^\n.,;]{0,40}?"
    r"\b(?:цен[а-я]*|стоимост[а-я]*|расценк[а-я]*|предложени[а-я]*|котировк[а-я]*|прайс[а-я]*)\b",
    r"\bсообщите\s+(?:пожалуйста\s+)?(?:вашу\s+)?(?:цену|стоимость|расценки)\b",
    r"\bпришли(?:те)?\s+прайс[а-я]*\b",
    r"\bпришли(?:те)?\s+кп\b",
    r"\bвыставить\s+кп\b",
    r"\bналичи[а-я]*\s+и\s+цен[а-я]*\b",
    r"\bцен[а-я]*\s+и\s+наличи[а-я]*\b",
    r"\bтребу(?:ется|ются)\s+(?:запчаст[а-я]*|детал[а-я]*|поставк[а-я]*)\b",
    r"\bнужны?\s+запчаст[а-я]*\b",
    r"\bавиазапчаст[а-я]*\b",
    r"\bсколько\s+сто[ий]т\b",
    r"\bсколько\s+буд(?:ет)?\s+сто[ий]ть\b",
    r"\bотдел\s+закупок\b",
    r"\bдепартамент\s+закупок\b",
    r"\bслужба\s+снабжени[а-я]*\b",
    r"\bотдел\s+снабжени[а-я]*\b",
)

BODY_RFQ_RE = re.compile(
    "(" + "|".join(_BODY_DIRECT_EN + _BODY_IMPLICIT_EN + _BODY_DIRECT_RU + _BODY_IMPLICIT_RU) + ")",
    flags=re.IGNORECASE | re.DOTALL,
)

_SUBJECT_KEYWORDS = (
    r"\brfq\b",
    r"\brfp\b",
    r"\brequest\s+for\s+(?:quotation|quote|proposal)s?\b",
    r"\bquotation\b",
    r"\bquote\b",
    r"\bprice\s+request\b",
    r"\bpricing\s+request\b",
    r"\bpurchase\s+inquiry\b",
    r"\bparts?\s+(?:required|inquiry|request)\b",
    r"\btender\b",
    r"\baog\b",
    r"\bзапрос[а-я]*\s+(?:предложен[а-я]*|котировк[а-я]*|цен[а-я]*)\b",
    r"\bзаявк[а-я]*\b",
    r"\bкоммерческ(?:ое|ого|ому)?\s+предложени[а-я]*\b",
    r"\bкотировк[а-я]*\b",
    r"\bпрайс[а-я]*\b",
    r"\bтендер[а-я]*\b",
)

SUBJECT_RFQ_RE = re.compile("(" + "|".join(_SUBJECT_KEYWORDS) + ")", flags=re.IGNORECASE)

# Filenames rarely use spaces (e.g. "RFQ_PN12345.xlsx", "ЗапросКотировки.pdf"),
# so word-boundary matching is dropped in favor of plain (case-insensitive)
# substring search over the short, fairly specific tokens below.
_ATTACHMENT_NAME_KEYWORDS = (
    r"rfq",
    r"rfp",
    r"quot(?:e|ation)",
    r"request",
    r"inquiry",
    r"tender",
    r"price[-_ ]?list",
    r"parts?[-_ ]?list",
    r"запрос",
    r"заявк",
    r"прайс",
    r"котировк",
    r"тендер",
)

ATTACHMENT_NAME_RFQ_RE = re.compile("|".join(_ATTACHMENT_NAME_KEYWORDS), flags=re.IGNORECASE)


def domain_of_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized:
        return ""
    return normalized.rsplit("@", 1)[1]


def client_id_for_sender(sender_email: str, allowed_domains: dict[str, int]) -> int | None:
    return allowed_domains.get(domain_of_email(sender_email))


def is_allowed_sender(sender_email: str, allowed_domains: dict[str, int]) -> bool:
    return client_id_for_sender(sender_email, allowed_domains) is not None


def is_allowed_attachment(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_ATTACHMENT_SUFFIXES


def filter_allowed_attachments(attachments: list[Attachment]) -> list[Attachment]:
    return [attachment for attachment in attachments if is_allowed_attachment(attachment.filename)]


def _has_rfq_like_attachment(attachments: list[Attachment]) -> bool:
    return any(
        ATTACHMENT_NAME_RFQ_RE.search(attachment.filename) for attachment in filter_allowed_attachments(attachments)
    )


def is_rfq_email(subject: str, body: str, attachments: list[Attachment] | None = None) -> bool:
    if SUBJECT_RFQ_RE.search(subject or ""):
        return True

    if BODY_RFQ_RE.search(body or ""):
        return True

    return _has_rfq_like_attachment(attachments or [])


def should_process_email(message: EmailMessage, allowed_domains: dict[str, int]) -> bool:
    is_message_sender_allowed = is_allowed_sender(message.sender_email, allowed_domains)
    is_message_rfq = is_rfq_email(message.subject, message.body, message.attachments)

    if not is_message_sender_allowed:
        logger.info(f"message sender is not allowed")
        return False
    if not is_message_rfq:
        logger.info(f"message is not rfq")
        return False
    
    return True
