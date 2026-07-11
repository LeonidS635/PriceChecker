"""Tests for extractor.anonymizer.gliner — the quotation anonymizer.

Two tiers:

1. UNIT TESTS (default, fast, no model): exercise every deterministic
   layer in isolation - protection extraction, PII regexes, chunking,
   filters, overlap resolution, merge/quotes/expansion/propagation
   post-processing, and the splicing. These encode the *contract*:
   above all, "part numbers are NEVER redacted".

2. INTEGRATION TESTS (opt-in, slow, downloads/loads GLiNER ~900MB):
   run the full anonymize() pipeline on realistic RU/EN/mixed quotations
   and assert part-number survival + PII redaction end-to-end.

Run:
    cd backend/services/rfq-service/extractor
    pytest tests/test_anonymizer.py -v
    RUN_MODEL_TESTS=1 pytest tests/test_anonymizer.py -v
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from extractor.anonymizer.gliner import (
    MAX_CHUNK_CHARS,
    GLiNERAnonymizer,
    Span,
    _absorb_quotes,
    _chunk_lines,
    _company_candidates,
    _expand_address_cells,
    _extract_protected_terms,
    _filter_ml_candidates,
    _is_bare_code,
    _is_mergeable_gap,
    _looks_like_real_phone,
    _merge_adjacent,
    _propagate,
    _protected_spans,
    _regex_candidates,
    _resolve_overlaps,
)

RUN_MODEL_TESTS = os.environ.get("RUN_MODEL_TESTS") == "1"


def ml(start, end, type_, score=0.5):
    return Span(start, end, type_, score, priority=0)


def rx(start, end, type_):
    return Span(start, end, type_, 1.0, priority=1)


# ============================================================
# Layer 1: protection of part numbers / descriptions
# ============================================================

class TestProtectedTerms(unittest.TestCase):
    def test_markdown_table_part_column(self):
        text = (
            "| Item | Partnumber | Description |\n"
            "|---|---|---|\n"
            "| 1 | 630-1001-384 | CAP ASSY |\n"
            "| 2 | BACC2C3D01878EG | CABLE ASSY |\n"
        )
        terms = _extract_protected_terms(text)
        self.assertIn("630-1001-384", terms)
        self.assertIn("BACC2C3D01878EG", terms)
        self.assertIn("CAP ASSY", terms)  # descriptions protected too

    def test_russian_headers(self):
        text = (
            "| № | Номер детали | Описание |\n"
            "|---|---|---|\n"
            "| 1 | АВ-123/4 | КЛАПАН |\n"
        )
        terms = _extract_protected_terms(text)
        self.assertIn("АВ-123/4", terms)
        self.assertIn("КЛАПАН", terms)

    def test_repeated_headers_mid_table(self):
        # Real quotations repeat the header row per item (page breaks).
        text = (
            "|Item|Partnumber|\n"
            "|---|---|\n"
            "|1|111-AAA|\n"
            "|Item|Partnumber|\n"
            "|2|222-BBB|\n"
        )
        terms = _extract_protected_terms(text)
        self.assertIn("111-AAA", terms)
        self.assertIn("222-BBB", terms)

    def test_bold_cells(self):
        text = (
            "|**Item**|**Partnumber**|\n"
            "|---|---|\n"
            "|**1**|**251A2190-2**|\n"
        )
        self.assertIn("251A2190-2", _extract_protected_terms(text))

    def test_inline_pn_mentions(self):
        for snippet, expected in [
            ("alt. p/n: 251A2184-3", "251A2184-3"),
            ("Part Number 630-1001-384 required", "630-1001-384"),
            ("артикул: АВ-99/1", "АВ-99/1"),
            ("P/N BACC2C3D01878EG", "BACC2C3D01878EG"),
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(expected, _extract_protected_terms(snippet))

    def test_alternate_pn_column_with_semicolon_list(self):
        text = (
            "| Part Number | Alternate PN |\n"
            "|---|---|\n"
            "| 1211318-003 | 1211318-004; 1339M80P03 |\n"
        )
        terms = _extract_protected_terms(text)
        self.assertIn("1211318-003", terms)
        # The whole alternates list is protected as one cell value.
        self.assertIn("1211318-004; 1339M80P03", terms)

    def test_protected_spans_all_occurrences(self):
        text = "PN 111-AAA here, and 111-AAA again"
        spans = _protected_spans(text, {"111-AAA"})
        self.assertEqual(len(spans), 2)


# ============================================================
# Layer 2: deterministic PII regexes
# ============================================================

class TestRegexPII(unittest.TestCase):
    def _types(self, text):
        return {(text[s.start:s.end], s.type) for s in _regex_candidates(text)}

    def test_email(self):
        found = self._types("write to Ivan.Petrov@utair.ru please")
        self.assertIn(("Ivan.Petrov@utair.ru", "EMAIL"), found)

    def test_urls(self):
        found = self._types("see https://romashka.ru/x and www.belavia.by.")
        self.assertIn(("https://romashka.ru/x", "URL"), found)
        self.assertIn(("www.belavia.by", "URL"), found)

    def test_bare_domain(self):
        found = self._types("Website: belavia.by")
        self.assertIn(("belavia.by", "URL"), found)

    def test_phone_with_plus(self):
        found = self._types("call +375 999 87 65 43 now")
        self.assertIn(("+375 999 87 65 43", "PHONE"), found)

    def test_phone_with_keyword(self):
        found = self._types("тел. 8 (495) 123-45-67")
        self.assertTrue(any(t == "PHONE" for _, t in found))

    # --- THE core requirement: part-number shapes are NOT phones ---

    def test_bare_digit_dash_is_not_phone(self):
        # "8-800-999-00" without tel/fax context or '+' must NOT match:
        # this exact shape is a legal part number.
        self.assertFalse(_regex_candidates("Pump 8-800-999-00 qty 2"))

    def test_part_numbers_produce_no_candidates(self):
        for pn in ["630-1001-384", "251A2190-2", "BACC2C3D01878EG",
                   "1339M80P03", "АВ-123/4"]:
            with self.subTest(pn=pn):
                self.assertFalse(_regex_candidates(f"item {pn} qty 2"))

    def test_phone_after_pn_keyword_not_matched_by_context_regex(self):
        # 'p/n' is not a phone keyword.
        self.assertFalse(
            [s for s in _regex_candidates("p/n: 111-22-33") if s.type == "PHONE"]
        )


# ============================================================
# Known-company deny-list
# ============================================================

class TestKnownCompanies(unittest.TestCase):
    def _values(self, text):
        return {text[s.start:s.end] for s in _company_candidates(text)}

    def test_full_legal_forms_matched_whole(self):
        cases = [
            'нужд ПАО "Авиакомпания "ЮТэйр". Во вложении',
            "needs of UTair Aviation PJSC. In the attachment",
            "APPROVED BY POBEDA AIRLINES LLC PRIOR TO",
            "company Belavia-Belarusian Airlines here",
            "from Aeroflot - Russian Airlines today",
        ]
        expected = [
            'ПАО "Авиакомпания "ЮТэйр"',
            "UTair Aviation PJSC",
            "POBEDA AIRLINES LLC",
            "Belavia-Belarusian Airlines",
            "Aeroflot - Russian Airlines",
        ]
        for text, want in zip(cases, expected):
            with self.subTest(text=text):
                self.assertIn(want, self._values(text))

    def test_short_forms_and_casing(self):
        for text, want in [
            ("Sincerely, UTair", "UTair"),
            ("от Ютэйр по запросу", "Ютэйр"),
            ("сайт аэрофлот тут", "аэрофлот"),
            ("BELAVIA quotation", "BELAVIA"),
        ]:
            with self.subTest(text=text):
                self.assertIn(want, self._values(text))

    def test_ambiguous_pobeda_needs_context(self):
        # Plain noun usage must NOT match...
        self.assertFalse(self._values("это большая победа команды"))
        # ...but quoted / airline-context usage must.
        self.assertTrue(self._values('рейс АК "Победа" отменен'))
        self.assertTrue(self._values("авиакомпания Победа сообщает"))
        self.assertTrue(self._values('ООО «Победа» уведомляет'))

    def test_unlisted_company_not_matched(self):
        # Deny-list is additive: unknown companies are the ML layer's job.
        self.assertFalse(self._values("Some Random Aerosupply Ltd"))


# ============================================================
# Chunking
# ============================================================

class TestChunking(unittest.TestCase):
    def test_offsets_reconstruct_text(self):
        text = "\n".join(f"line {i} " + "x" * 40 for i in range(50))
        chunks = _chunk_lines(text)
        self.assertEqual("".join(c for _, c in chunks), text)
        pos = 0
        for off, chunk in chunks:
            self.assertEqual(off, pos)
            pos += len(chunk)

    def test_chunk_size_respected(self):
        text = "\n".join("word " * 20 for _ in range(30))
        for _, chunk in _chunk_lines(text):
            self.assertLessEqual(len(chunk), MAX_CHUNK_CHARS)

    def test_long_single_line_split_on_br(self):
        line = "<br>".join(f"segment {i} data" for i in range(60))
        chunks = _chunk_lines(line)
        self.assertGreater(len(chunks), 1)
        self.assertEqual("".join(c for _, c in chunks), line)

    def test_no_split_inside_token(self):
        # A pathological line with no spaces/<br> still reconstructs.
        line = "A" * 1000
        chunks = _chunk_lines(line)
        self.assertEqual("".join(c for _, c in chunks), line)


# ============================================================
# ML candidate filters
# ============================================================

class TestFilters(unittest.TestCase):
    def test_phone_with_letters_rejected(self):
        text = "part BACC2C3D01878EG here"
        span = ml(5, 20, "PHONE")
        self.assertFalse(_looks_like_real_phone(text, span))

    def test_phone_without_context_rejected(self):
        text = "item 630-1001-384 qty"
        span = ml(5, 17, "PHONE")
        self.assertFalse(_looks_like_real_phone(text, span))

    def test_phone_with_plus_accepted(self):
        text = "call +375 999 87 65 43"
        span = ml(5, 22, "PHONE")
        self.assertTrue(_looks_like_real_phone(text, span))

    def test_phone_with_keyword_accepted(self):
        text = "тел: 8 495 123 45 67"
        span = ml(5, 20, "PHONE")
        self.assertTrue(_looks_like_real_phone(text, span))

    def test_bare_code_shapes(self):
        for code in ["251A2190-2", "BACC2C3D01878EG", "11C/1", "Д.2/3"]:
            with self.subTest(code=code):
                self.assertTrue(_is_bare_code(code.replace("Д.", "Д-")))
        for not_code in ["Иван Петров", "ООО Ромашка", "MOSCOW"]:
            with self.subTest(not_code=not_code):
                self.assertFalse(_is_bare_code(not_code))

    def test_decoy_types_dropped(self):
        text = "x" * 40
        spans = [ml(0, 5, "PART_NUMBER"), ml(10, 15, "CERTIFICATE"),
                 ml(20, 25, "JOB_TITLE"), ml(30, 35, "PERSON")]
        kept = _filter_ml_candidates(text, spans, [], [])
        self.assertEqual([s.type for s in kept], ["PERSON"])

    def test_protected_overlap_dropped(self):
        text = "part 630-1001-384 here"
        spans = [ml(5, 17, "PHONE", 0.9)]
        kept = _filter_ml_candidates(text, spans, [(5, 17)], [])
        self.assertFalse(kept)

    def test_domain_allow_overlap_dropped(self):
        text = "requires MFG CofC form"
        spans = [ml(9, 17, "COMPANY", 0.9)]
        allow = [(9, 12), (13, 17)]
        kept = _filter_ml_candidates(text, spans, [], allow)
        self.assertFalse(kept)

    def test_decoy_suppresses_weaker_pii_guess(self):
        text = "FAA 8130-3 form"
        spans = [ml(0, 10, "CERTIFICATE", 0.8), ml(0, 10, "COMPANY", 0.4)]
        kept = _filter_ml_candidates(text, spans, [], [])
        self.assertFalse(kept)

    def test_generic_terms_dropped(self):
        cases = [("Поставщик", "PERSON"), ("Вы", "PERSON"),
                 ("адрес", "ADDRESS"), ("supplier", "PERSON"),
                 ("С уважением", "PERSON")]
        for value, type_ in cases:
            with self.subTest(value=value):
                kept = _filter_ml_candidates(
                    value, [ml(0, len(value), type_, 0.9)], [], []
                )
                self.assertFalse(kept)

    def test_postal_code_must_be_digits(self):
        kept = _filter_ml_candidates("ab-12", [ml(0, 5, "POSTAL_CODE", 0.9)], [], [])
        self.assertFalse(kept)
        kept = _filter_ml_candidates("123456", [ml(0, 6, "POSTAL_CODE", 0.9)], [], [])
        self.assertEqual(len(kept), 1)

    def test_real_person_kept(self):
        text = "Contact: Ivan Petrov"
        kept = _filter_ml_candidates(text, [ml(9, 20, "PERSON", 0.9)], [], [])
        self.assertEqual(len(kept), 1)


# ============================================================
# Overlap resolution
# ============================================================

class TestOverlaps(unittest.TestCase):
    def test_regex_beats_ml(self):
        # PERSON matched inside an email: EMAIL (regex) must win.
        spans = [ml(0, 11, "PERSON", 0.95), rx(0, 17, "EMAIL")]
        resolved = _resolve_overlaps(spans)
        self.assertEqual([s.type for s in resolved], ["EMAIL"])

    def test_longer_span_wins(self):
        spans = [ml(0, 10, "ADDRESS", 0.9), ml(0, 25, "ADDRESS", 0.5)]
        resolved = _resolve_overlaps(spans)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].end, 25)

    def test_higher_score_wins_same_length(self):
        spans = [ml(0, 10, "PHONE", 0.4), ml(0, 10, "URL", 0.7)]
        resolved = _resolve_overlaps(spans)
        self.assertEqual(resolved[0].type, "URL")

    def test_disjoint_spans_all_kept(self):
        spans = [ml(0, 5, "PERSON"), ml(10, 15, "COMPANY")]
        self.assertEqual(len(_resolve_overlaps(spans)), 2)


# ============================================================
# Post-processing: merge / quotes / expansion / propagation
# ============================================================

class TestMerge(unittest.TestCase):
    def test_person_fragments_merge(self):
        text = "Responsible: Ivanov, Petr"
        spans = [ml(13, 20, "PERSON"), ml(21, 25, "PERSON")]
        merged = _merge_adjacent(spans, text, [])
        self.assertEqual(len(merged), 1)
        self.assertEqual(text[merged[0].start:merged[0].end], "Ivanov, Petr")

    def test_address_merges_across_house_number(self):
        text = "УЛ. КОЛОТУШКИНА, Д.1, КВ. 29, МОСКВА"
        spans = [ml(0, 12, "ADDRESS"), ml(27, 33, "ADDRESS")]
        merged = _merge_adjacent(spans, text, [])
        self.assertEqual(len(merged), 1)

    def test_no_merge_across_cell_border(self):
        text = "Ivanov | Petrov"
        spans = [ml(0, 6, "PERSON"), ml(9, 15, "PERSON")]
        self.assertEqual(len(_merge_adjacent(spans, text, [])), 2)

    def test_no_merge_across_newline(self):
        text = "Ivanov\nPetrov"
        spans = [ml(0, 6, "PERSON"), ml(7, 13, "PERSON")]
        self.assertEqual(len(_merge_adjacent(spans, text, [])), 2)

    def test_no_merge_of_different_types(self):
        text = "Ivanov, Moscow"
        spans = [ml(0, 6, "PERSON"), ml(8, 14, "ADDRESS")]
        self.assertEqual(len(_merge_adjacent(spans, text, [])), 2)

    def test_merge_never_swallows_protected_part_number(self):
        # Two ADDRESS guesses with a protected PN in the gap: the PN
        # is digit-bearing (qualifies as address glue) but must survive.
        text = "Moscow 251A2190-2 Tver"
        spans = [ml(0, 6, "ADDRESS"), ml(18, 22, "ADDRESS")]
        merged = _merge_adjacent(spans, text, [(7, 17)])
        self.assertEqual(len(merged), 2)

    def test_word_gap_blocks_merge(self):
        text = "Ivanov works Petrov"
        spans = [ml(0, 6, "PERSON"), ml(13, 19, "PERSON")]
        self.assertEqual(len(_merge_adjacent(spans, text, [])), 2)

    def test_gap_rules(self):
        self.assertTrue(_is_mergeable_gap(", ", "PERSON"))
        self.assertTrue(_is_mergeable_gap(", Д.2/3, КВ. ", "ADDRESS"))
        self.assertFalse(_is_mergeable_gap(" | ", "ADDRESS"))
        self.assertFalse(_is_mergeable_gap("<br>", "ADDRESS"))
        self.assertFalse(_is_mergeable_gap(" словами ", "ADDRESS"))
        self.assertFalse(_is_mergeable_gap(" street ", "PERSON"))


class TestQuotes(unittest.TestCase):
    def test_absorbs_closing_quote(self):
        text = 'ПАО "Авиакомпания "Ютэйр"'
        spans = [ml(0, 24, "COMPANY")]  # model clipped the final quote
        out = _absorb_quotes(spans, text)
        self.assertEqual(text[out[0].start:out[0].end], text)

    def test_no_quotes_no_change(self):
        text = "UTair Aviation PJSC"
        spans = [ml(0, 19, "COMPANY")]
        out = _absorb_quotes(spans, text)
        self.assertEqual((out[0].start, out[0].end), (0, 19))

    def test_balanced_quotes_untouched(self):
        text = 'x "ООО Ромашка" y'
        spans = [ml(2, 15, "COMPANY")]  # already includes both quotes
        out = _absorb_quotes(spans, text)
        self.assertEqual(text[out[0].start:out[0].end], '"ООО Ромашка"')


class TestAddressExpansion(unittest.TestCase):
    def test_high_coverage_expands_to_cell(self):
        text = "| Priority | УЛ. КОЛОТУШКИНА, Д.2/3, МОСКВА, РОССИЯ |"
        addr = text.index("УЛ.")
        spans = [ml(addr, addr + 29, "ADDRESS")]  # ~73% of the cell
        out = _expand_address_cells(spans, text, [])
        value = text[out[0].start:out[0].end]
        self.assertIn("РОССИЯ", value)

    def test_low_coverage_not_expanded(self):
        text = "| deliver the goods directly to our Moscow warehouse ASAP |"
        m = text.index("Moscow")
        spans = [ml(m, m + 6, "ADDRESS")]
        out = _expand_address_cells(spans, text, [])
        self.assertEqual(text[out[0].start:out[0].end], "Moscow")

    def test_expansion_blocked_by_protected(self):
        text = "| MOSCOW STREET 5 630-1001-384 |"
        spans = [ml(2, 17, "ADDRESS")]
        pn = text.index("630")
        out = _expand_address_cells(spans, text, [(pn, pn + 12)])
        self.assertEqual((out[0].start, out[0].end), (2, 17))

    def test_non_address_untouched(self):
        text = "| Ivan Petrov Petrovich |"
        spans = [ml(2, 13, "PERSON")]
        out = _expand_address_cells(spans, text, [])
        self.assertEqual((out[0].start, out[0].end), (2, 13))


class TestPropagation(unittest.TestCase):
    def test_duplicated_cells_all_redacted(self):
        cell = 'ООО "СКАЙТЕХ"'
        text = f"| {cell} | {cell} | {cell} |"
        first = text.index(cell)
        spans = [ml(first, first + len(cell), "COMPANY")]
        out = _propagate(spans, text, [], [])
        self.assertEqual(len(out), 3)

    def test_short_values_not_propagated(self):
        # "AM" (country code cell) is too short - propagating it would
        # hit every "AM" substring in the document.
        text = "| AM | AM | AMSTERDAM PROGRAM |"
        spans = [ml(2, 4, "ADDRESS")]
        out = _propagate(spans, text, [], [])
        self.assertEqual(len(out), 1)

    def test_propagation_respects_word_boundaries(self):
        text = "Igor here and Igorevich there"
        spans = [ml(0, 4, "PERSON")]
        out = _propagate(spans, text, [], [])
        self.assertEqual(len(out), 1)  # "Igorevich" not hit

    def test_propagation_skips_protected(self):
        text = "MOSCOW city | Partnumber MOSCOW-1"
        pn = text.index("MOSCOW-1")
        spans = [ml(0, 6, "ADDRESS")]
        out = _propagate(spans, text, [(pn, pn + 8)], [])
        self.assertEqual(len(out), 1)


# ============================================================
# End-to-end splicing with mocked model (no GLiNER load)
# ============================================================

class TestAnonymizeMocked(unittest.TestCase):
    """Full anonymize() with _gliner_candidates monkeypatched, verifying
    orchestration + splicing without paying for model inference."""

    def setUp(self):
        self.anonymizer = GLiNERAnonymizer()
        self.fake_spans: list[Span] = []
        self.gliner_patcher = patch(
            "extractor.anonymizer.gliner._gliner_candidates",
            lambda text, model, thr: list(self.fake_spans),
        )
        self.gliner_patcher.start()
        self.model_patcher = patch.object(
            self.anonymizer,
            "_ensure_loaded",
            return_value=MagicMock(),
        )
        self.model_patcher.start()

    def tearDown(self):
        self.gliner_patcher.stop()
        self.model_patcher.stop()

    def test_part_number_never_redacted_even_if_model_insists(self):
        text = (
            "| Partnumber |\n"
            "|---|\n"
            "| 630-1001-384 |\n"
        )
        pn = text.index("630-1001-384")
        # Model is maximally confused: tags the PN as everything at once.
        self.fake_spans = [
            ml(pn, pn + 12, "PHONE", 0.99),
            ml(pn, pn + 12, "PERSON", 0.99),
            ml(pn, pn + 12, "ADDRESS", 0.99),
        ]
        self.assertIn("630-1001-384", self.anonymizer.anonymize(text))

    def test_curly_brace_tags(self):
        text = "Contact: Ivan Petrov and x@y.com"
        self.fake_spans = [ml(9, 20, "PERSON", 0.9)]
        result = self.anonymizer.anonymize(text)
        self.assertIn("{PERSON}", result)
        self.assertIn("{EMAIL}", result)
        self.assertNotIn("<PERSON>", result)
        self.assertNotIn("Ivan", result)

    def test_email_regex_beats_person_fragment(self):
        text = "mail: ivan.petrov@utair.ru now"
        self.fake_spans = [ml(6, 17, "PERSON", 0.95)]  # "ivan.petrov"
        result = self.anonymizer.anonymize(text)
        self.assertIn("mail: {EMAIL} now", result)

    def test_no_entities_text_unchanged(self):
        text = "FOR EXPENDABLES - one of the above mentioned\n"
        self.fake_spans = []
        self.assertEqual(self.anonymizer.anonymize(text), text)

    def test_markdown_table_structure_preserved(self):
        text = (
            "| Partnumber | Qty |\n"
            "|---|---|\n"
            "| 251A2190-2 | 2 |\n"
        )
        self.fake_spans = []
        result = self.anonymizer.anonymize(text)
        self.assertEqual(result.count("|"), text.count("|"))
        self.assertIn("251A2190-2", result)


# ============================================================
# Integration tests (real model) - opt-in via RUN_MODEL_TESTS=1
# ============================================================

@unittest.skipUnless(RUN_MODEL_TESTS, "set RUN_MODEL_TESTS=1 to run")
class TestIntegrationRealModel(unittest.TestCase):
    """The behavioural baseline on realistic documents. Every part number
    must survive; every piece of PII must disappear."""

    @classmethod
    def setUpClass(cls):
        cls.anonymizer = GLiNERAnonymizer()
        cls.anonymizer.warmup()  # fail fast if the model can't load

    def check(self, text, must_survive, must_disappear):
        result = self.anonymizer.anonymize(text)
        for item in must_survive:
            self.assertIn(item, result, f"PAYLOAD LOST: {item!r}")
        for item in must_disappear:
            self.assertNotIn(item, result, f"PII LEAKED: {item!r}")

    def test_english_quotation(self):
        text = (
            "Request for Quotation\n\n"
            "| Description | Part Number | Qty |\n"
            "|---|---|---|\n"
            "| Pump | 8-800-456-11 | 2 |\n"
            "| Filter | AX-12345-US | 10 |\n\n"
            "Contact: John Smith\n"
            "Tel: +1 202 555 0143\n"
            "Email: j.smith@acmeaero.com\n"
            "Website: www.acmeaero.com\n"
        )
        self.check(
            text,
            must_survive=["8-800-456-11", "AX-12345-US", "Pump", "Filter"],
            must_disappear=["John Smith", "+1 202 555 0143",
                            "j.smith@acmeaero.com", "www.acmeaero.com"],
        )

    def test_russian_quotation(self):
        text = (
            "Запрос котировки\n\n"
            "| Наименование | Номер детали | Кол-во |\n"
            "|---|---|---|\n"
            "| НАСОС | 8-800-456-11 | 2 |\n\n"
            "Контакт: Петров Иван\n"
            "тел. +7 495 123-45-67\n"
            "email: petrov@romashka.ru\n"
        )
        self.check(
            text,
            must_survive=["8-800-456-11", "НАСОС"],
            must_disappear=["Петров Иван", "+7 495 123-45-67",
                            "petrov@romashka.ru"],
        )

    def test_mixed_language_with_ocr_block(self):
        text = (
            "# Q1607126\n\n"
            "Number / Номер: Q1607126<br>SUPPLIER Поставщик<br>"
            "ACME AIRLINES LLC<br>GREENWAY ROAD 7, 12345 - BERLIN<br>"
            "Responsible: Meier, Hans<br>Email: h.meier@acmeair.de<br>\n\n"
            "|**Item**|**Partnumber**|**Description**|\n"
            "|---|---|---|\n"
            "|**1**|**251A2190-2**|**SPRING-OUTER**|\n"
            "|**2**|**BACC2C3D01878EG**|**CABLE ASSY WSA2-R**|\n\n"
            "**Item 2 Text alt. p/n: 251A2184-3**\n"
        )
        self.check(
            text,
            must_survive=["Q1607126", "251A2190-2", "BACC2C3D01878EG",
                          "251A2184-3", "SPRING-OUTER", "CABLE ASSY WSA2-R"],
            must_disappear=["h.meier@acmeair.de"],
        )

    def test_part_number_next_to_phone_same_shape(self):
        # THE hard case: same digit pattern, one is a PN in a table,
        # the other is an explicit phone contact.
        text = (
            "| Part Number | Qty |\n"
            "|---|---|\n"
            "| 8-800-123-45 | 2 |\n\n"
            "Tel: 8-800-123-45 (office)\n"
        )
        result = self.anonymizer.anonymize(text)
        # The table copy must survive (propagation must NOT kill it even
        # though an identical string appears in phone context).
        self.assertIn("| 8-800-456-11 |", result)

    def test_duplicated_supplier_cells_consistent(self):
        cell = 'ООО "АВИАДЕТАЛЬ"'
        text = (
            f"| SUPPLIER: | {cell} | {cell} | {cell} |\n"
            "|---|---|---|---|\n"
        )
        result = self.anonymizer.anonymize(text)
        self.assertNotIn("АВИАДЕТАЛЬ", result)

    def test_no_angle_bracket_tags_in_output(self):
        text = "Contact: John Smith, j.smith@x.com"
        result = self.anonymizer.anonymize(text)
        self.assertNotIn("<PERSON>", result)
        self.assertNotIn("<EMAIL>", result)
