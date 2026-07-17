"""Anonymize aviation RFQ / quotation documents before sending them to an LLM.

Sensitive data (persons, companies, addresses, postal codes, emails, URLs,
phone numbers) is replaced with {TAG} placeholders. No mapping is kept.

Hard requirement: part numbers must NEVER be anonymized.
A false positive on a part number is unacceptable; a leaked phone number is
merely undesirable. Every heuristic below is therefore biased in favour of
keeping part-number-shaped text intact.

Architecture — three independent layers, each doing only what it is good at:

1. Deterministic PROTECTION (the zero-false-positive guarantee for parts):
   * markdown table columns whose header looks like "Partnumber" / "P/N" /
     "номер детали" / "артикул" — every cell value in such a column,
   * columns headed "Description" / "описание" / "наименование" — item
     descriptions are payload data the downstream LLM needs, never PII,
   * inline mentions like "alt. p/n: 251A2184-3".
   Each collected term is protected at EVERY occurrence in the document.
   No candidate entity overlapping a protected span is ever redacted
   (emails/URLs excepted — '@' and dotted domains cannot be part numbers).

2. Deterministic PII (precise regexes — cheaper and stricter than ML):
   * KNOWN COMPANIES deny-list: quotations are known to come from a fixed
     set of airlines; their names are matched by regex and expanded over
     legal-form affixes (ПАО/ООО/"Авиакомпания .../LLC/PJSC) and quotes.
     This is ADDITIVE: the ML layer still catches companies not on the list.
   * emails, URLs, phones anchored by '+' or tel/fax keywords.

3. GLiNER (urchade/gliner_multi-v2.1) for entities that need context:
   person, company name, address, postal code. Decoy labels ("part number",
   "certificate", "job title") attract alphanumeric codes and aviation forms
   so they do not leak into person/company; decoy matches are dropped.

Post-filters, overlap resolution, and post-processing (merge / quotes /
cell expansion / propagation) are described at the relevant functions below.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Optional

if TYPE_CHECKING:
    from gliner import GLiNER

logger = logging.getLogger(__name__)

# ============================================================
# Configuration
# ============================================================

MODEL_NAME = "urchade/gliner_multi-v2.1"
# 0.3 rather than a stricter value: recall on Cyrillic names/companies
# needs it, and false positives on part numbers are prevented by the
# deterministic protection layer + shape filters, not by the threshold.
DEFAULT_THRESHOLD = 0.3
# Small line-aligned chunks. Empirically GLiNER's confidence collapses on
# long mixed-content chunks (a person name scoring 0.91 in its own
# paragraph drops to 0.20 inside a 600-char chunk), so short chunks are a
# recall requirement, not just a token-window precaution.
MAX_CHUNK_CHARS = 250

# GLiNER zero-shot labels -> internal entity types.
# "part number", "certificate" and "job title" are decoys: they attract
# spans that would otherwise leak into person/company (alphanumeric codes,
# aviation form names like "FAA 8130-3", titles like "Marketing
# Specialist") and are then discarded, leaving that text untouched.
GLINER_LABEL_TO_TYPE = {
    "person": "PERSON",
    "company name": "COMPANY",
    "address": "ADDRESS",
    "postal code": "POSTAL_CODE",
    "phone number": "PHONE",
    "part number": "PART_NUMBER",
    "certificate": "CERTIFICATE",
    "job title": "JOB_TITLE",
}
GLINER_LABELS = list(GLINER_LABEL_TO_TYPE)
# Decoy types are never anonymized; they also suppress overlapping PII
# candidates that scored lower than the decoy.
DECOY_TYPES = {"PART_NUMBER", "CERTIFICATE", "JOB_TITLE"}

# Generic words GLiNER sometimes tags as person/company/address. Redacting
# them loses information and gains nothing — they identify nobody:
# role words, greetings/closings, pronouns, and meta-words (the literal
# word "адрес"/"address" in "отправьте на адрес..." is not an address).
GENERIC_TERMS = {
    # roles
    "supplier", "customer", "buyer", "seller", "colleagues", "dear colleagues",
    "поставщик", "заказчик", "покупатель", "продавец", "коллеги",
    "уважаемые коллеги", "dear",
    # greetings / closings
    "с уважением", "sincerely", "best regards", "regards", "thanks",
    # pronouns / forms of address
    "вы", "вас", "вам", "ваш", "ваше", "вашему", "you", "your",
    "вашему вниманию", "your attention",
    # meta-words: field labels are not their values
    "address", "адрес", "адреса", "e-mail", "email", "почта", "сайт",
    "website", "tel", "phone", "телефон", "тел", "факс", "fax",
}

# Known airline counterparties. Deterministic deny-list on top of the ML:
# short unambiguous cores; casing handled by IGNORECASE, legal forms and
# quotes by _expand_company_affixes(). Longest alias wins the alternation.
KNOWN_COMPANY_ALIASES = [
    # UTair
    "UTair Aviation", "UTair", "ЮТэйр",
    # Pobeda (Cyrillic "Победа" is ambiguous -> _AMBIGUOUS_COMPANY_RE)
    "Pobeda Airlines", "Pobeda", "flypobeda",
    # Belavia
    "Belavia-Belarusian Airlines", "Belavia", "Белавиа",
    # Aeroflot
    "Aeroflot - Russian Airlines", "Aeroflot", "Аэрофлот",
]

# Cyrillic "Победа" doubles as the common noun "victory": treat it as the
# airline only when quoted («Победа») or after "авиакомпания"/"АК".
_AMBIGUOUS_COMPANY_RE = re.compile(
    r'(?:(?<=["«“])Победа(?=["»”])'
    r'|(?<![А-Яа-яЁёA-Za-z])(?:авиакомпани[яию]|АК)\s+["«“]?Победа["»”]?)',
    re.IGNORECASE,
)

# Legal-form / affix words absorbed around a matched company core so that
# 'ПАО "Авиакомпания "ЮТэйр"' or 'POBEDA AIRLINES LLC' is redacted whole.
_COMPANY_PRE_WORDS = {"пао", "оао", "зао", "ао", "ооо", "ак", "авиакомпания"}
_COMPANY_POST_WORDS = {
    "llc", "pjsc", "jsc", "ltd", "inc", "plc", "co", "gmbh",
    "airlines", "airline", "aviation",
}


def _build_company_regex(aliases: Iterable[str]) -> re.Pattern:
    parts = sorted((re.escape(a) for a in aliases), key=len, reverse=True)
    return re.compile(
        r"(?<![A-Za-zА-Яа-яЁё0-9])(?:" + "|".join(parts) + r")(?![A-Za-zА-Яа-яЁё0-9])",
        re.IGNORECASE,
    )


_KNOWN_COMPANY_RE = _build_company_regex(KNOWN_COMPANY_ALIASES)

# Aviation-domain vocabulary that must never be redacted: certification
# forms and related abbreviations that GLiNER occasionally mistakes for
# company names ("MFG CofC" scored 0.80 as a company). Terms, not spans:
# any candidate overlapping an occurrence of these words is dropped.
_DOMAIN_ALLOW_RE = re.compile(
    r"\b(?:CofC|C\.?O\.?C\.?|EASA|FAA|TCCA|CAAC|ATA[-\s]?106|8130-3|MFG"
    r"|ФАП|АТА[-\s]?106)\b",
    re.IGNORECASE,
)

# Curly braces, not <>: angle-bracket tags are parsed as HTML by markdown
# and can be silently dropped by renderers/parsers the LLM pipeline uses.
TAGS = {
    "PERSON": "{PERSON}",
    "COMPANY": "{COMPANY}",
    "ADDRESS": "{ADDRESS}",
    "POSTAL_CODE": "{POSTAL_CODE}",
    "PHONE": "{PHONE}",
    "EMAIL": "{EMAIL}",
    "URL": "{URL}",
}

# Characters treated as "glue" between two same-type spans when merging.
_GLUE_CHARS = set(" \t,.;:-–—/\"'«»“”()")
_QUOTE_CHARS = "\"'«»“”"
# Segment delimiters for cell expansion: markdown cell border, <br>, newline.
_SEGMENT_DELIMS_RE = re.compile(r"\||<br\s*/?>|\n")

# ============================================================
# Regexes
# ============================================================

# Table headers whose column values must be protected (part numbers and
# item descriptions — both are payload the downstream LLM needs).
_PROTECTED_HEADER_RE = re.compile(
    r"part\s*num(?:ber)?|part\s*no\b|\bp\s*/?\s*n\b|партномер|номер\s+детали"
    r"|артикул|descri|наименование|описание",
    re.IGNORECASE,
)

# Inline "p/n: 251A2184-3", "part number 630-1001-384", "артикул: ...".
# Cyrillic included: Russian documents do carry Cyrillic артикулы/ГОСТ codes,
# and protecting them is the safe direction (protection can only prevent
# redaction, never cause it).
_INLINE_PN_RE = re.compile(
    r"(?:\bp\s*/?\s*n\b|part\s*number|part\s*no\b|партномер|номер\s+детали|артикул)"
    r"\s*[:#.]?\s*([A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9\-/]{2,})",
    re.IGNORECASE,
)

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

# Scheme- or www-prefixed URLs.
_URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s|<>\"')]+", re.IGNORECASE)
# Bare lowercase domains with a whitelisted TLD ("belavia.by"). Lowercase
# only on purpose: part numbers are conventionally uppercase and never
# contain dots, so this cannot collide with them.
_BARE_DOMAIN_RE = re.compile(
    r"\b[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?(?:\.[a-z0-9\-]+)*"
    r"\.(?:ru|su|by|com|net|org|info|aero|io|kz|ua|de|fr|cn|us|uk|рф)\b"
)

# Phone anchored by a context keyword.
_PHONE_CTX_RE = re.compile(
    r"(?:\b(?:tel|fax|phone|mob(?:ile)?|cell|viber|whatsapp)\b|тел(?:ефон)?|факс|моб)"
    r"\s*\.?\s*:?\s*(\+?\s?\d[\d\s\-().]{5,}\d)",
    re.IGNORECASE,
)
# International phone: part numbers never start with '+'.
_PHONE_INTL_RE = re.compile(r"\+\s?\d[\d\s\-().]{5,}\d")

# Keyword shortly before a GLiNER-proposed phone span.
_PHONE_CTX_WORD_RE = re.compile(
    r"(?:tel|fax|phone|mob|cell|viber|whatsapp|тел|факс|моб|звон)", re.IGNORECASE
)

_ANY_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁё]")
# Bare alphanumeric-dash/slash code, e.g. "251A2190-2", "BACC2C3D01878EG".
_CODE_SHAPE_RE = re.compile(
    r"[A-Za-zА-Яа-яЁё0-9]+(?:[-/][A-Za-zА-Яа-яЁё0-9]+)*"
)
_TABLE_FILLER_RE = re.compile(r"[\s\-:]*")


@dataclass
class Span:
    start: int
    end: int
    type: str
    score: float
    priority: int  # 1 = deterministic regex, 0 = ML

    def overlaps(self, start: int, end: int) -> bool:
        return self.start < end and start < self.end


# ============================================================
# Layer 1: deterministic protection of part numbers & descriptions
# ============================================================

def _clean_cell(cell: str) -> str:
    return cell.strip().strip("*`").strip()


def _extract_protected_terms(text: str) -> set[str]:
    """Part numbers / descriptions from markdown tables + inline p/n mentions."""
    terms: set[str] = set()

    for match in _INLINE_PN_RE.finditer(text):
        terms.add(match.group(1).strip("*`. "))

    protected_cols: list[int] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.count("|") >= 2):
            protected_cols = []  # left the table
            continue

        cells = [_clean_cell(c) for c in stripped.strip("|").split("|")]

        # Header rows may repeat mid-table (page breaks, per-item blocks).
        header_cols = [
            i for i, c in enumerate(cells) if _PROTECTED_HEADER_RE.search(c)
        ]
        if header_cols:
            protected_cols = header_cols
            continue
        if all(_TABLE_FILLER_RE.fullmatch(c) for c in cells):
            continue  # |---|---| separator or empty row

        for idx in protected_cols:
            if idx < len(cells):
                value = cells[idx]
                if value and not _TABLE_FILLER_RE.fullmatch(value):
                    terms.add(value)

    return {t for t in terms if len(t) >= 2}


def _protected_spans(text: str, terms: Iterable[str]) -> list[tuple[int, int]]:
    """Every occurrence of every protected term, document-wide."""
    spans: list[tuple[int, int]] = []
    for term in terms:
        for match in re.finditer(re.escape(term), text):
            spans.append((match.start(), match.end()))
    return spans


# ============================================================
# Layer 2: deterministic PII (regex)
# ============================================================

def _regex_candidates(text: str) -> list[Span]:
    candidates: list[Span] = []

    for match in _EMAIL_RE.finditer(text):
        candidates.append(Span(match.start(), match.end(), "EMAIL", 1.0, 1))

    for regex in (_URL_RE, _BARE_DOMAIN_RE):
        for match in regex.finditer(text):
            end = match.end()
            while end > match.start() and text[end - 1] in ".,;)]}\"'":
                end -= 1  # trim trailing punctuation
            candidates.append(Span(match.start(), end, "URL", 1.0, 1))

    for match in _PHONE_CTX_RE.finditer(text):
        candidates.append(Span(match.start(1), match.end(1), "PHONE", 1.0, 1))
    for match in _PHONE_INTL_RE.finditer(text):
        candidates.append(Span(match.start(), match.end(), "PHONE", 1.0, 1))

    return candidates


def _expand_company_affixes(text: str, start: int, end: int) -> tuple[int, int]:
    """Grow a matched company core over its legal-form dressing:
    'ЮТэйр' inside 'ПАО "Авиакомпания "ЮТэйр"' -> the whole thing;
    'Pobeda Airlines' inside 'POBEDA AIRLINES LLC' -> with the LLC."""
    changed = True
    while changed:
        changed = False
        while end < len(text) and text[end] in _QUOTE_CHARS:
            end += 1
            changed = True
        m = re.match(r"[ \t]+(?:[-–—][ \t]*)?([A-Za-zА-Яа-яЁё.]+)", text[end:])
        if m and m.group(1).rstrip(".").lower() in _COMPANY_POST_WORDS:
            end += m.end()
            changed = True
    changed = True
    while changed:
        changed = False
        while start > 0 and text[start - 1] in _QUOTE_CHARS:
            start -= 1
            changed = True
        m = re.search(r"([A-Za-zА-Яа-яЁё.]+)(?:[ \t]*[-–—])?[ \t]+$", text[:start])
        if m and m.group(1).rstrip(".").lower() in _COMPANY_PRE_WORDS:
            start = m.start()
            changed = True
    # A sentence-final period is not part of the name ("... PJSC. In the").
    while end > start and text[end - 1] == ".":
        end -= 1
    return start, end


def _company_candidates(text: str) -> list[Span]:
    """Deterministic known-company spans (deny-list, KNOWN_COMPANY_ALIASES).

    Additive to the ML path, which still catches companies not on the
    list. To support a new counterparty, add it to KNOWN_COMPANY_ALIASES.
    """
    spans: list[Span] = []
    for rx_ in (_KNOWN_COMPANY_RE, _AMBIGUOUS_COMPANY_RE):
        for m in rx_.finditer(text):
            s, e = _expand_company_affixes(text, m.start(), m.end())
            spans.append(Span(s, e, "COMPANY", 1.0, 1))
    return spans


# ============================================================
# Layer 3: GLiNER
# ============================================================

def _split_long_line(line: str) -> list[str]:
    """A single line longer than MAX_CHUNK_CHARS (e.g. OCR "picture text"
    glued together with <br>) would silently exceed GLiNER's token window,
    so break it at <br> tags or whitespace, never inside a token."""
    pieces: list[str] = []
    rest = line
    while len(rest) > MAX_CHUNK_CHARS:
        window = rest[:MAX_CHUNK_CHARS]
        cut = window.rfind("<br>")
        if cut > 0:
            cut += len("<br>")
        else:
            cut = window.rfind(" ")
        if cut <= 0:
            cut = MAX_CHUNK_CHARS
        pieces.append(rest[:cut])
        rest = rest[cut:]
    if rest:
        pieces.append(rest)
    return pieces


def _chunk_lines(text: str) -> list[tuple[int, str]]:
    """Split into (offset, chunk) pieces on line boundaries so table rows
    and sentences are never cut in the middle. Oversized single lines are
    further split at <br>/whitespace boundaries."""
    pieces: list[str] = []
    for line in text.splitlines(keepends=True):
        if len(line) > MAX_CHUNK_CHARS:
            pieces.extend(_split_long_line(line))
        else:
            pieces.append(line)

    chunks: list[tuple[int, str]] = []
    start = 0
    pos = 0
    for piece in pieces:
        if pos > start and (pos - start) + len(piece) > MAX_CHUNK_CHARS:
            chunks.append((start, text[start:pos]))
            start = pos
        pos += len(piece)
    if pos > start:
        chunks.append((start, text[start:pos]))
    return chunks


def _gliner_candidates(text: str, model: "GLiNER", threshold: float) -> list[Span]:
    candidates: list[Span] = []
    for offset, chunk in _chunk_lines(text):
        for ent in model.predict_entities(chunk, GLINER_LABELS, threshold=threshold):
            candidates.append(
                Span(
                    start=offset + ent["start"],
                    end=offset + ent["end"],
                    type=GLINER_LABEL_TO_TYPE[ent["label"]],
                    score=float(ent["score"]),
                    priority=0,
                )
            )
    return candidates


# ============================================================
# Filtering and overlap resolution
# ============================================================

def _digit_count(s: str) -> int:
    return sum(ch.isdigit() for ch in s)


def _norm_term(value: str) -> str:
    return value.strip().strip("\"'«»“”,.:;!* ").lower()


def _looks_like_real_phone(text: str, span: Span) -> bool:
    """Accept an ML 'phone' guess only with strong evidence it is not a
    part number: no letters, >=7 digits, and either a leading '+' or a
    tel/fax-style keyword shortly before the span."""
    value = text[span.start : span.end].strip()
    if _ANY_LETTER_RE.search(value):
        return False
    if _digit_count(value) < 7:
        return False
    if value.startswith("+"):
        return True
    context = text[max(0, span.start - 30) : span.start]
    return bool(_PHONE_CTX_WORD_RE.search(context))


def _is_bare_code(value: str) -> bool:
    """Alphanumeric-dash/slash token containing a digit — part number shape."""
    value = value.strip()
    return bool(_CODE_SHAPE_RE.fullmatch(value)) and any(c.isdigit() for c in value)


def _filter_ml_candidates(
    text: str,
    candidates: list[Span],
    protected: list[tuple[int, int]],
    allow: list[tuple[int, int]],
) -> list[Span]:
    decoys = [s for s in candidates if s.type in DECOY_TYPES]

    kept: list[Span] = []
    for span in candidates:
        value = text[span.start : span.end].strip()

        if span.type in DECOY_TYPES:
            continue  # decoy labels: leave the text untouched

        # Anything overlapping a protected part number / description or a
        # domain-vocabulary term is sacrosanct, whatever the model thinks.
        if any(span.overlaps(s, e) for s, e in protected):
            continue
        if any(span.overlaps(s, e) for s, e in allow):
            continue

        # A decoy tagged the same text with equal/higher confidence ->
        # trust the decoy interpretation (when in doubt, don't redact).
        if any(
            span.overlaps(d.start, d.end) and d.score >= span.score for d in decoys
        ):
            continue

        if _norm_term(value) in GENERIC_TERMS:
            continue

        if span.type == "PHONE" and not _looks_like_real_phone(text, span):
            continue

        if span.type == "POSTAL_CODE" and not re.fullmatch(r"\d{4,9}", value):
            continue

        # A bare digit-bearing code tagged as person/company/address is
        # almost certainly a mislabelled part/order number.
        if span.type in ("PERSON", "COMPANY", "ADDRESS") and _is_bare_code(value):
            continue

        kept.append(span)
    return kept


def _resolve_overlaps(spans: list[Span]) -> list[Span]:
    """One winner per overlapping group: deterministic regex beats ML,
    then longer span, then higher score."""

    def better(a: Span, b: Span) -> bool:
        if a.priority != b.priority:
            return a.priority > b.priority
        if (a.end - a.start) != (b.end - b.start):
            return (a.end - a.start) > (b.end - b.start)
        return a.score > b.score

    resolved: list[Span] = []
    for span in sorted(spans, key=lambda s: (s.start, -(s.end - s.start))):
        conflict = next(
            (i for i, kept in enumerate(resolved) if span.overlaps(kept.start, kept.end)),
            None,
        )
        if conflict is None:
            resolved.append(span)
        elif better(span, resolved[conflict]):
            resolved[conflict] = span
    return resolved


# ============================================================
# Post-processing: merge / quotes / cell expansion / propagation
# ============================================================

def _is_mergeable_gap(gap: str, span_type: str) -> bool:
    """Can two same-type spans be fused across this gap? Only punctuation
    and spaces qualify; for ADDRESS also short digit-bearing tokens
    and 1-3 letter abbreviations ("УЛ", "КВ", "Д") that models chronically
    skip inside addresses. Never across newlines, table borders or <br> —
    those separate cells."""
    if any(c in gap for c in "\n|") or "<br" in gap:
        return False
    rest = "".join(c for c in gap if c not in _GLUE_CHARS)
    if not rest:
        return True
    if span_type == "ADDRESS":
        tokens = [t for t in re.split(r"[\s,.;:/\-]+", gap) if t]
        return all(
            len(t) <= 12 and (any(c.isdigit() for c in t) or len(t) <= 3)
            for t in tokens
        )
    return False


def _merge_adjacent(
    spans: list[Span], text: str, protected: list[tuple[int, int]]
) -> list[Span]:
    """Fuse same-type fragments: '{ADDRESS}, {ADDRESS}' -> one
    span; 'Litonin, Igor' as two PERSONs -> one PERSON. A merge never
    swallows a protected span (part numbers are digit-bearing and would
    otherwise qualify as ADDRESS glue)."""
    ordered = sorted(spans, key=lambda s: s.start)
    merged: list[Span] = []
    for span in ordered:
        if (
            merged
            and merged[-1].type == span.type
            and span.start >= merged[-1].end
            and _is_mergeable_gap(text[merged[-1].end : span.start], span.type)
            # protected span inside/overlapping the gap -> no merge
            and not any(
                s < span.start and merged[-1].end < e for s, e in protected
            )
        ):
            prev = merged[-1]
            merged[-1] = Span(
                prev.start, span.end, prev.type,
                max(prev.score, span.score), max(prev.priority, span.priority),
            )
        else:
            merged.append(span)
    return merged


def _absorb_quotes(spans: list[Span], text: str) -> list[Span]:
    """'ПАО "Компания' + trailing '"' -> include the closing quote so the
    output has no dangling quote artifacts."""
    out: list[Span] = []
    for span in spans:
        start, end = span.start, span.end
        for _ in range(4):
            value = text[start:end]
            if not any(q in value for q in _QUOTE_CHARS):
                break
            grew = False
            if end < len(text) and text[end] in _QUOTE_CHARS:
                end += 1
                grew = True
            if start > 0 and text[start - 1] in _QUOTE_CHARS:
                start -= 1
                grew = True
            if not grew:
                break
        out.append(Span(start, end, span.type, span.score, span.priority))
    return out


def _segment_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """Bounds of the table cell / <br>-segment / line containing [start,end)."""
    seg_start = 0
    for m in _SEGMENT_DELIMS_RE.finditer(text, 0, start):
        seg_start = m.end()
    m = _SEGMENT_DELIMS_RE.search(text, end)
    seg_end = m.start() if m else len(text)
    while seg_start < seg_end and text[seg_start] in " *\t":
        seg_start += 1
    while seg_end > seg_start and text[seg_end - 1] in " *\t":
        seg_end -= 1
    return seg_start, seg_end


def _expand_address_cells(
    spans: list[Span],
    text: str,
    protected: list[tuple[int, int]],
    coverage: float = 0.6,
) -> list[Span]:
    """An ADDRESS covering >= `coverage` of its cell expands to the whole
    cell: models chronically clip the house number / country off an
    address, and the leftover fragment both leaks data and is noise."""
    out: list[Span] = []
    for span in spans:
        if span.type != "ADDRESS":
            out.append(span)
            continue
        seg_start, seg_end = _segment_bounds(text, span.start, span.end)
        seg_len = seg_end - seg_start
        if seg_len <= 0 or (span.end - span.start) / seg_len < coverage:
            out.append(span)
            continue
        if any(
            s < seg_end and seg_start < e and not (span.start <= s and e <= span.end)
            for s, e in protected
        ):
            out.append(span)  # expansion would swallow protected payload
            continue
        if any(
            o is not span and o.overlaps(seg_start, seg_end) and o.type != span.type
            for o in spans
        ):
            out.append(span)  # e.g. an EMAIL lives in the same cell
            continue
        out.append(Span(seg_start, seg_end, span.type, span.score, span.priority))
    return out


def _propagate(
    spans: list[Span],
    text: str,
    protected: list[tuple[int, int]],
    allow: list[tuple[int, int]],
) -> list[Span]:
    """Redact every identical occurrence of every redacted value.

    Duplicated table cells are scored independently by the model; one
    copy leaking while its twin is redacted is a leak AND makes the
    document inconsistent. Deterministic string equality — cannot
    introduce new false positives beyond what was already redacted.
    """
    values: dict[str, Span] = {}
    for span in spans:
        value = text[span.start : span.end].strip()
        has_letter = bool(_ANY_LETTER_RE.search(value))
        if (len(value) >= 4 and has_letter) or (len(value) >= 6 and not has_letter):
            values.setdefault(value, span)

    extra: list[Span] = []
    for value, src in values.items():
        pattern = re.escape(value)
        if value[0].isalnum():
            pattern = r"(?<![A-Za-z0-9А-Яа-яЁё])" + pattern
        if value[-1].isalnum():
            pattern = pattern + r"(?![A-Za-z0-9А-Яа-яЁё])"
        for m in re.finditer(pattern, text):
            s, e = m.span()
            if any(s < pe and ps < e for ps, pe in protected):
                continue
            if any(s < ae and as_ < e for as_, ae in allow):
                continue
            hit = [o for o in spans + extra if o.overlaps(s, e)]
            if any(h.type != src.type or h.start < s or h.end > e for h in hit):
                continue  # conflicts with a different/wider existing span
            if any(h.start == s and h.end == e for h in hit):
                continue  # already redacted
            extra.append(Span(s, e, src.type, src.score, src.priority))
    return spans + extra


def _anonymize_text(
    text: str,
    model: "GLiNER",
    threshold: float,
) -> str:
    protected_terms = _extract_protected_terms(text)
    protected = _protected_spans(text, protected_terms)
    allow = [m.span() for m in _DOMAIN_ALLOW_RE.finditer(text)]

    regex_spans = _regex_candidates(text)
    # Known-company deny-list: deterministic, but part numbers still rank
    # higher — a match overlapping a protected span is discarded.
    regex_spans += [
        s
        for s in _company_candidates(text)
        if not any(s.overlaps(ps, pe) for ps, pe in protected)
    ]
    ml_spans = _filter_ml_candidates(
        text, _gliner_candidates(text, model, threshold), protected, allow
    )

    spans = _resolve_overlaps(regex_spans + ml_spans)
    spans = _merge_adjacent(spans, text, protected)
    spans = _absorb_quotes(spans, text)
    spans = _merge_adjacent(spans, text, protected)  # quotes may join spans
    spans = _expand_address_cells(spans, text, protected)
    spans = _propagate(spans, text, protected, allow)
    final = _resolve_overlaps(spans)  # expansion may have created overlaps

    result = text
    for span in sorted(final, key=lambda s: s.start, reverse=True):
        tag = TAGS.get(span.type, "{" + span.type + "}")
        result = result[: span.start] + tag + result[span.end :]
    return result


class GLiNERAnonymizer:
    """GLiNER-based anonymizer for aviation RFQ documents.

    The model is loaded on first use (``anonymize`` or ``warmup``). Call
    ``warmup()`` at service startup to pay the load cost before the first
    NATS message arrives. Docker build pre-downloads weights to disk so
    ``from_pretrained`` does not hit the network, but still loads tensors
    into RAM on first use.
    """

    def __init__(self, threshold: float = DEFAULT_THRESHOLD, device: str = "cpu") -> None:
        self._threshold = threshold
        self._device = device
        self._model: Optional["GLiNER"] = None

    def _ensure_loaded(self) -> "GLiNER":
        if self._model is None:
            from gliner import GLiNER

            logger.info(
                "Loading GLiNER model %s on device=%s (this may take a moment)",
                MODEL_NAME,
                self._device,
            )
            self._model = GLiNER.from_pretrained(
                MODEL_NAME, local_files_only=True, low_cpu_mem_usage=True,
            ).to(self._device)
            logger.info("GLiNER model loaded")
        return self._model

    def warmup(self) -> None:
        """Load the model and run a minimal inference pass.

        Use at process startup so the first real document is not delayed by
        weight loading and PyTorch initialisation.
        """
        model = self._ensure_loaded()
        model.predict_entities("warmup", GLINER_LABELS, threshold=self._threshold)
        logger.info("GLiNER warmup complete")

    def anonymize(self, text: str) -> str:
        if not text.strip():
            return text

        return _anonymize_text(text, self._ensure_loaded(), self._threshold)
