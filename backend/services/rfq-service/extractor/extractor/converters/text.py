from __future__ import annotations

import io
import logging
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_DOCX_HEADING_MAP = {
    "Title": 1,
    "Heading 1": 1,
    "Heading 2": 2,
    "Heading 3": 3,
    "Heading 4": 4,
    "Heading 5": 5,
    "Heading 6": 6,
}


def to_text(data: bytes, content_type: str, filename: str | None = None) -> str | None:
    """Convert raw file bytes to a Markdown-formatted string.

    Returns None when the file type is unrecognised or conversion fails.
    Markdown output preserves document structure (headings, tables, lists)
    so that downstream LLM processing can reason about layout correctly.
    """
    ct = content_type.lower().split(";")[0].strip()
    ext = Path(filename).suffix.lower() if filename else ""

    if ct in ("text", "plain", "text/plain") or ext == ".txt":
        return _decode(data)

    if ct in ("html", "text/html") or ext in (".html", ".htm"):
        return _from_html(data)

    if ct in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ) or ext in (".docx", ".doc"):
        return _from_word(data, ext, ct)

    if ct in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/vnd.ms-excel.sheet.macroEnabled.12",
    ) or ext in (".xlsx", ".xls", ".xlsm"):
        return _from_excel(data, ext, ct)

    if ct in ("application/pdf",) or ext == ".pdf":
        return _from_pdf(data)

    logger.warning("Unsupported content type %r (filename=%r), skipping", content_type, filename)
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decode(data: bytes) -> str:
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _convert_with_libreoffice(data: bytes, source_ext: str, target_format: str) -> bytes | None:
    """Convert legacy Office formats via headless LibreOffice, if available."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / f"input{source_ext}"
        tmp_path.write_bytes(data)
        cmd = [
            "soffice",
            "--headless",
            "--convert-to",
            target_format,
            "--outdir",
            tmp_dir,
            str(tmp_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("LibreOffice conversion unavailable: %s", exc)
            return None

        if result.returncode != 0:
            logger.warning(
                "LibreOffice conversion failed (%s -> %s): %s",
                source_ext,
                target_format,
                result.stderr.strip(),
            )
            return None

        converted = Path(tmp_dir) / f"input.{target_format}"
        if not converted.exists():
            logger.warning("LibreOffice did not produce expected output: %s", converted)
            return None

        return converted.read_bytes()


# ---------------------------------------------------------------------------
# HTML / PDF
# ---------------------------------------------------------------------------

def _from_html(data: bytes) -> str:
    from markdownify import markdownify

    return markdownify(_decode(data), heading_style="ATX", bullets="-")


def _from_pdf(data: bytes) -> str:
    import fitz
    import pymupdf4llm

    doc = fitz.open(stream=data, filetype="pdf")
    return pymupdf4llm.to_markdown(doc)


# ---------------------------------------------------------------------------
# Word (DOC/DOCX)
# ---------------------------------------------------------------------------

def _from_word(data: bytes, ext: str, ct: str = "") -> str | None:
    if ext == ".doc" or (not ext and ct == "application/msword"):
        converted = _convert_with_libreoffice(data, ".doc", "docx")
        if converted is None:
            return None
        data = converted

    return _convert_docx_bytes(data)


def _convert_docx_bytes(data: bytes) -> str:
    from docx import Document
    from docx.document import Document as _Document
    from docx.oxml.ns import qn
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table, _Cell
    from docx.text.paragraph import Paragraph

    def iter_block_items(parent):
        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("Unsupported parent type for DOCX block iteration")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    document = Document(io.BytesIO(data))
    md_blocks: list[str] = []
    list_counters: dict[int, int] = {}

    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            md = _docx_paragraph_to_markdown(block, list_counters, qn)
            if md:
                md_blocks.append(md)
        elif isinstance(block, Table):
            list_counters.clear()
            md_table = _docx_table_to_markdown(block)
            if md_table:
                md_blocks.extend(("", md_table, ""))

    return "\n\n".join(block for block in md_blocks if block != "")


def _docx_is_list_paragraph(paragraph, qn) -> bool:
    p_pr = paragraph._p.pPr
    if p_pr is not None and p_pr.find(qn("w:numPr")) is not None:
        return True
    style_name = (paragraph.style.name or "").lower()
    return "list" in style_name


def _docx_is_ordered_list(paragraph) -> bool:
    style_name = (paragraph.style.name or "").lower()
    return "number" in style_name


def _docx_render_runs(paragraph) -> str:
    parts: list[str] = []
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue
        if run.bold and run.italic:
            text = f"***{text}***"
        elif run.bold:
            text = f"**{text}**"
        elif run.italic:
            text = f"*{text}*"
        parts.append(text)
    return "".join(parts) if parts else paragraph.text


def _docx_paragraph_to_markdown(paragraph, list_counters: dict[int, int], qn) -> str:
    text = _docx_render_runs(paragraph).strip()
    if not text:
        return ""

    style_name = paragraph.style.name or ""

    if style_name in _DOCX_HEADING_MAP:
        level = _DOCX_HEADING_MAP[style_name]
        return f"{'#' * level} {text}"

    if _docx_is_list_paragraph(paragraph, qn):
        indent_level = 0
        p_pr = paragraph._p.pPr
        ilvl_el = p_pr.find(qn("w:numPr") + "/" + qn("w:ilvl")) if p_pr is not None else None
        if ilvl_el is not None:
            indent_level = int(ilvl_el.get(qn("w:val")) or 0)
        indent = "  " * indent_level

        if _docx_is_ordered_list(paragraph):
            list_counters[indent_level] = list_counters.get(indent_level, 0) + 1
            return f"{indent}{list_counters[indent_level]}. {text}"
        return f"{indent}- {text}"

    list_counters.clear()
    return text


def _docx_table_to_markdown(table) -> str:
    rows_text: list[list[str]] = []
    for row in table.rows:
        cells_text: list[str] = []
        for cell in row.cells:
            cell_text = " ".join(p.text.strip() for p in cell.paragraphs if p.text.strip())
            cell_text = cell_text.replace("|", "\\|").replace("\n", " ")
            cells_text.append(cell_text)
        rows_text.append(cells_text)

    if not rows_text:
        return ""

    n_cols = max(len(row) for row in rows_text)
    for row in rows_text:
        while len(row) < n_cols:
            row.append("")

    header, *body = rows_text
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * n_cols) + " |",
        *("| " + " | ".join(row) + " |" for row in body),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Excel (XLS/XLSX)
# ---------------------------------------------------------------------------

def _from_excel(data: bytes, ext: str, ct: str = "") -> str | None:
    if ext == ".xls" or (not ext and ct == "application/vnd.ms-excel"):
        converted = _convert_with_libreoffice(data, ".xls", "xlsx")
        if converted is None:
            return None
        data = converted

    return _convert_xlsx_bytes(data)


def _format_excel_cell_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime) and (value.hour or value.minute or value.second):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return repr(value)
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _build_excel_grid(sheet, fill_merged: bool, range_boundaries):
    max_row = sheet.max_row
    max_col = sheet.max_column
    grid = [
        [_format_excel_cell_value(sheet.cell(row, col).value) for col in range(1, max_col + 1)]
        for row in range(1, max_row + 1)
    ]

    if fill_merged:
        for merged_range in sheet.merged_cells.ranges:
            min_col, min_row, max_col_m, max_row_m = range_boundaries(str(merged_range))
            top_left_value = grid[min_row - 1][min_col - 1]
            for row in range(min_row, max_row_m + 1):
                for col in range(min_col, max_col_m + 1):
                    grid[row - 1][col - 1] = top_left_value

    return grid


def _excel_row_is_empty(row) -> bool:
    return all(cell == "" for cell in row)


def _excel_row_is_caption(row) -> bool:
    non_empty = [cell for cell in row if cell != ""]
    return len(non_empty) == 1


def _split_excel_into_blocks(raw_grid, filled_grid):
    blocks: list[dict[str, object]] = []
    current_rows: list[list[str]] = []
    pending_caption: str | None = None

    def flush() -> None:
        nonlocal current_rows, pending_caption
        if current_rows:
            blocks.append({"caption": pending_caption, "rows": current_rows})
        current_rows = []
        pending_caption = None

    for raw_row, filled_row in zip(raw_grid, filled_grid):
        if _excel_row_is_empty(raw_row):
            flush()
            continue
        if not current_rows and _excel_row_is_caption(raw_row):
            pending_caption = next(cell for cell in raw_row if cell != "")
            continue
        current_rows.append(filled_row)

    flush()
    return blocks


def _excel_rows_to_markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""

    n_cols = max(len(row) for row in rows)
    norm_rows = [row + [""] * (n_cols - len(row)) for row in rows]

    while n_cols > 1 and all(row[n_cols - 1] == "" for row in norm_rows):
        norm_rows = [row[:-1] for row in norm_rows]
        n_cols -= 1

    header, *body = norm_rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * n_cols) + " |",
        *("| " + " | ".join(row) + " |" for row in body),
    ]
    return "\n".join(lines)


def _convert_xlsx_bytes(data: bytes, fill_merged: bool = True) -> str:
    from openpyxl import load_workbook
    from openpyxl.utils import range_boundaries

    workbook = load_workbook(io.BytesIO(data), data_only=True)
    md_blocks: list[str] = []

    for sheet in workbook.worksheets:
        if sheet.sheet_state != "visible":
            continue

        md_blocks.append(f"## {sheet.title}")

        if sheet.max_row == 0 or sheet.max_column == 0:
            md_blocks.append("_(пустой лист)_")
            continue

        raw_grid = _build_excel_grid(sheet, fill_merged=False, range_boundaries=range_boundaries)
        filled_grid = _build_excel_grid(sheet, fill_merged=fill_merged, range_boundaries=range_boundaries)
        blocks = _split_excel_into_blocks(raw_grid, filled_grid)

        if not blocks:
            md_blocks.append("_(пустой лист)_")
            continue

        for block in blocks:
            caption = block["caption"]
            if caption:
                md_blocks.append(f"### {caption}")
            table_md = _excel_rows_to_markdown_table(block["rows"])
            if table_md:
                md_blocks.append(table_md)

    return "\n\n".join(md_blocks)
