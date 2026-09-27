"""PDF/DOCX -> source_sections.

Splits an uploaded onboarding manual into sections at its headings, keeping
page numbers so every enhanced passage can point back to where it came from.
The text is extracted as-is (tables become markdown, bullets become "- "); the
parser never rewrites content.

PDF pages are exact. DOCX has no fixed pages, so DOCX page numbers count page
breaks (explicit breaks plus the ones Word records when it last laid out the
document) and are approximate.
"""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass, field

import pymupdf
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

pymupdf.no_recommend_layout()  # silence the stdout hint printed by find_tables

MAX_PAGES = 200
# A DOCX is a zip archive; refuse ones that unpack far larger than any real manual (zip bombs).
MAX_DOCX_UNZIPPED_BYTES = 200 * 1024 * 1024
MAX_DOCX_ENTRIES = 5000

BULLET_CHARS = "•◦▪▫‣∙●○■□–"
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}
# A wrapped line ending in one of these continues the same token (URL, path, compound word).
JOIN_WITHOUT_SPACE = ("-", "/", "\\", "_")


class ParseError(Exception):
    """The file can't be turned into sections (corrupt, empty, scanned, too long)."""


@dataclass
class SourceSection:
    ordinal: int
    heading: str | None
    content: str
    page_start: int
    page_end: int


@dataclass
class ParsedManual:
    page_count: int
    sections: list[SourceSection]


def parse_manual(data: bytes, file_type: str) -> ParsedManual:
    """Parse a manual's bytes. `file_type` is "pdf" or "docx"."""
    if file_type == "pdf":
        return _parse_pdf(data)
    if file_type == "docx":
        return _parse_docx(data)
    raise ParseError(f"Unsupported file type: {file_type}")


# ---------------------------------------------------------------------------
# Shared: turning a stream of headings and paragraphs into sections
# ---------------------------------------------------------------------------

@dataclass
class _Heading:
    text: str
    level: int  # 1 = top level
    page: int


@dataclass
class _Para:
    text: str
    page: int


@dataclass
class _Builder:
    """Collects headings and paragraphs in reading order and cuts sections at each heading."""

    sections: list[SourceSection] = field(default_factory=list)
    stack: list[_Heading] = field(default_factory=list)
    heading: str | None = None
    paras: list[_Para] = field(default_factory=list)
    heading_page: int | None = None

    def add_heading(self, h: _Heading) -> None:
        self._flush()
        while self.stack and self.stack[-1].level >= h.level:
            self.stack.pop()
        parent = self.stack[-1].text if self.stack else None
        self.stack.append(h)
        self.heading = f"{parent} › {h.text}" if parent else h.text
        self.heading_page = h.page

    def extend_heading(self, text: str) -> None:
        last = self.stack[-1]
        last.text = f"{last.text} {text}"
        parent = self.stack[-2].text if len(self.stack) > 1 else None
        self.heading = f"{parent} › {last.text}" if parent else last.text

    def add_para(self, p: _Para) -> None:
        if p.text.strip():
            self.paras.append(p)

    def finish(self) -> list[SourceSection]:
        self._flush()
        return self.sections

    def _flush(self) -> None:
        # A heading directly followed by a subheading produces no section of its
        # own; it still appears as the parent in the subheading's path.
        if self.paras:
            pages = [p.page for p in self.paras]
            start = min(pages + ([self.heading_page] if self.heading_page else []))
            self.sections.append(
                SourceSection(
                    ordinal=len(self.sections),
                    heading=self.heading,
                    content="\n\n".join(p.text for p in self.paras),
                    page_start=start,
                    page_end=max(pages),
                )
            )
        self.paras = []
        self.heading = None
        self.heading_page = None


def _clean(text: str) -> str:
    for lig, repl in LIGATURES.items():
        text = text.replace(lig, repl)
    text = unicodedata.normalize("NFC", text).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def _join_lines(lines: list[str]) -> str:
    out = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not out:
            out = line
        elif out.endswith(JOIN_WITHOUT_SPACE) and not out[:-1].endswith(" "):
            out += line
        else:
            out += " " + line
    return out


def _bullet(text: str) -> str:
    """Normalize a leading bullet glyph to markdown "- "."""
    if text and text[0] in BULLET_CHARS:
        return "- " + text[1:].strip()
    return text


def _table_markdown(rows: list[list[str | None]]) -> str:
    rows = [[_clean(_join_lines((c or "").splitlines())) for c in row] for row in rows]
    rows = [r for r in rows if any(r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

TEXT_FLAGS = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_LIGATURES & ~pymupdf.TEXT_PRESERVE_IMAGES
MARGIN_BAND = 0.08  # top/bottom share of the page where running headers and footers live


@dataclass
class _Line:
    text: str
    size: float
    bold: bool
    italic: bool
    bbox: tuple[float, float, float, float]
    block: int
    page: int


def _parse_pdf(data: bytes) -> ParsedManual:
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # pymupdf raises several types for bad files
        raise ParseError(f"Could not open PDF: {exc}") from exc
    if doc.needs_pass:
        raise ParseError("PDF is password protected")
    if doc.page_count > MAX_PAGES:
        raise ParseError(f"PDF has {doc.page_count} pages; the limit is {MAX_PAGES}")

    pages = [_pdf_page_items(page) for page in doc]
    lines = [item for items in pages for item in items if isinstance(item, _Line)]
    if sum(len(line.text) for line in lines) < 20:
        raise ParseError("No extractable text; the PDF may be scanned images")

    repeated = _running_text(doc, lines)
    body_size = _body_size(lines)
    levels = _heading_levels(lines, body_size, repeated)

    builder = _Builder()
    para: list[_Line] = []

    def flush_para():
        if para:
            builder.add_para(_Para(_bullet(_join_lines([ln.text for ln in para])), para[0].page))
            para.clear()

    prev: _Line | None = None
    prev_heading = False
    for items in pages:
        for item in items:
            if isinstance(item, _Para):  # a table, already rendered
                flush_para()
                builder.add_para(item)
                prev, prev_heading = None, False
                continue
            line = item
            if _norm_running(line.text) in repeated:
                continue
            level = levels.get(round(line.size, 1)) if _looks_like_heading(line, body_size) else None
            if level is not None:
                flush_para()
                wraps = (
                    prev_heading
                    and prev.block == line.block
                    and prev.page == line.page
                    and round(prev.size, 1) == round(line.size, 1)
                )
                if wraps:  # a heading that wrapped onto a second line
                    builder.extend_heading(line.text)
                else:
                    builder.add_heading(_Heading(line.text, level, line.page))
                prev, prev_heading = line, True
                continue
            if prev is None or prev_heading or prev.block != line.block or prev.page != line.page or line.text[0] in BULLET_CHARS:
                flush_para()
            para.append(line)
            prev, prev_heading = line, False
    flush_para()

    return ParsedManual(page_count=doc.page_count, sections=builder.finish())


def _pdf_page_items(page: pymupdf.Page) -> list[_Line | _Para]:
    """Lines and rendered tables for one page, in reading order."""
    page_no = page.number + 1
    tables = []
    try:
        tables = page.find_tables().tables
    except Exception:
        pass  # table detection is best effort; fall back to plain lines
    table_boxes = [pymupdf.Rect(t.bbox) for t in tables]
    links = [ln for ln in page.get_links() if ln.get("uri")]

    items: list[tuple[float, float, _Line | _Para]] = []
    for t, box in zip(tables, table_boxes):
        md = _table_markdown(t.extract())
        if md:
            items.append((box.y0, box.x0, _Para(md, page_no)))

    for block in page.get_text("dict", flags=TEXT_FLAGS, sort=True)["blocks"]:
        for raw in block.get("lines", []):
            spans = [s for s in raw["spans"] if s["text"].strip()]
            if not spans:
                continue
            bbox = pymupdf.Rect(raw["bbox"])
            if any(box.contains(pymupdf.Point((bbox.x0 + bbox.x1) / 2, (bbox.y0 + bbox.y1) / 2)) for box in table_boxes):
                continue
            text = _clean("".join(s["text"] for s in raw["spans"]))
            # Keep link targets whose visible text doesn't show the URL.
            for link in links:
                if bbox.intersects(link["from"]) and link["uri"] not in text:
                    text += f" ({link['uri']})"
            chars = sum(len(s["text"]) for s in spans)
            items.append((
                bbox.y0,
                bbox.x0,
                _Line(
                    text=text,
                    size=max(s["size"] for s in spans),
                    bold=sum(len(s["text"]) for s in spans if s["flags"] & 16 or "Bold" in s["font"]) > chars / 2,
                    italic=all(s["flags"] & 2 or "Italic" in s["font"] or "Oblique" in s["font"] for s in spans),
                    bbox=tuple(bbox),
                    block=block["number"],
                    page=page_no,
                ),
            ))

    # Stable sort by position keeps PyMuPDF's reading order for lines on the same row.
    items.sort(key=lambda it: (round(it[0]), it[1]))
    return [it[2] for it in items]


def _norm_running(text: str) -> str:
    return re.sub(r"\d+", "#", text.lower()).strip()


def _running_text(doc: pymupdf.Document, lines: list[_Line]) -> set[str]:
    """Headers/footers: text in the top or bottom margin repeated on most pages."""
    if doc.page_count < 3:
        return set()
    seen: dict[str, set[int]] = {}
    for line in lines:
        height = doc[line.page - 1].rect.height
        if line.bbox[1] < height * MARGIN_BAND or line.bbox[3] > height * (1 - MARGIN_BAND):
            seen.setdefault(_norm_running(line.text), set()).add(line.page)
    return {text for text, pages in seen.items() if len(pages) >= doc.page_count * 0.5}


def _body_size(lines: list[_Line]) -> float:
    sizes = Counter()
    for line in lines:
        sizes[round(line.size, 1)] += len(line.text)
    return sizes.most_common(1)[0][0]


def _looks_like_heading(line: _Line, body_size: float) -> bool:
    if len(line.text) > 120 or line.italic or line.text[0] in BULLET_CHARS:
        return False
    if line.size >= body_size * 1.4:
        return True
    return line.size >= body_size * 1.15 and line.bold


def _heading_levels(lines: list[_Line], body_size: float, repeated: set[str]) -> dict[float, int]:
    """Map heading font sizes to levels (largest = 1).

    A size used by exactly one line on the first page is the document title; it
    gets a level of its own so it doesn't become every section's parent.
    """
    candidates = [ln for ln in lines if _looks_like_heading(ln, body_size) and _norm_running(ln.text) not in repeated]
    by_size: dict[float, list[_Line]] = {}
    for ln in candidates:
        by_size.setdefault(round(ln.size, 1), []).append(ln)
    sizes = sorted(by_size, reverse=True)
    levels: dict[float, int] = {}
    level = 1
    for size in sizes:
        group = by_size[size]
        if size == sizes[0] and len(group) == 1 and group[0].page == 1 and len(sizes) > 1:
            levels[size] = 99  # title: never a parent of later headings
            continue
        levels[size] = level
        level += 1
    return levels


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def _check_docx_archive(data: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
    except zipfile.BadZipFile as exc:
        raise ParseError("Could not open DOCX: the file is damaged") from exc
    if len(entries) > MAX_DOCX_ENTRIES or sum(e.file_size for e in entries) > MAX_DOCX_UNZIPPED_BYTES:
        raise ParseError("This DOCX is too large to process")


def _parse_docx(data: bytes) -> ParsedManual:
    _check_docx_archive(data)
    try:
        doc = Document(io.BytesIO(data))
    except Exception as exc:  # python-docx raises several types for bad files
        raise ParseError(f"Could not open DOCX: {exc}") from exc

    builder = _Builder()
    numbering = _NumberingResolver(doc)
    page = 1
    chars = 0

    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            para = Paragraph(child, doc)
            if child.find(".//" + qn("w:pageBreakBefore")) is not None:
                page += 1
            text = _clean(_docx_paragraph_text(para))
            level = _docx_heading_level(para)
            if text:
                chars += len(text)
                if level is not None:
                    builder.add_heading(_Heading(text, level, page))
                else:
                    builder.add_para(_Para(numbering.prefix(para) + text, page))
            page += _docx_page_breaks(child)
        elif child.tag == qn("w:tbl"):
            table = Table(child, doc)
            md = _table_markdown([[cell.text for cell in row.cells] for row in table.rows])
            if md:
                chars += len(md)
                builder.add_para(_Para(md, page))
            page += _docx_page_breaks(child)

    if chars < 20:
        raise ParseError("The document has no text")
    if page > MAX_PAGES:
        raise ParseError(f"Document has about {page} pages; the limit is {MAX_PAGES}")
    return ParsedManual(page_count=page, sections=builder.finish())


def _docx_paragraph_text(para: Paragraph) -> str:
    text = para.text
    # Keep link targets whose visible text doesn't show the URL.
    for link in para.hyperlinks:
        url = link.url
        if url and url not in text:
            text = text.replace(link.text, f"{link.text} ({url})", 1) if link.text else f"{text} ({url})"
    return text


def _docx_heading_level(para: Paragraph) -> int | None:
    style = para.style
    while style is not None:
        name = (style.name or "").lower()
        if name == "title":
            return 99
        if m := re.fullmatch(r"heading (\d)", name):
            return int(m.group(1))
        style = style.base_style
    outline = para._p.find(f"{qn('w:pPr')}/{qn('w:outlineLvl')}")
    if outline is not None:
        return int(outline.get(qn("w:val"))) + 1
    return None


def _docx_page_breaks(el) -> int:
    explicit = sum(1 for br in el.iter(qn("w:br")) if br.get(qn("w:type")) == "page")
    rendered = sum(1 for _ in el.iter(qn("w:lastRenderedPageBreak")))
    # Word writes a rendered break next to an explicit one; don't count both.
    return max(explicit, rendered) if explicit and rendered else explicit + rendered


class _NumberingResolver:
    """Rebuilds "- " and "1. " prefixes for Word's automatic lists."""

    def __init__(self, doc):
        self.formats: dict[tuple[str, int], str] = {}
        self.counters: dict[tuple[str, int], int] = {}
        try:
            root = doc.part.numbering_part.element
        except (KeyError, NotImplementedError):
            return
        abstract = {}
        for a in root.findall(qn("w:abstractNum")):
            lvls = {}
            for lvl in a.findall(qn("w:lvl")):
                fmt = lvl.find(qn("w:numFmt"))
                lvls[int(lvl.get(qn("w:ilvl")))] = fmt.get(qn("w:val")) if fmt is not None else "bullet"
            abstract[a.get(qn("w:abstractNumId"))] = lvls
        for num in root.findall(qn("w:num")):
            ref = num.find(qn("w:abstractNumId"))
            for ilvl, fmt in abstract.get(ref.get(qn("w:val")) if ref is not None else None, {}).items():
                self.formats[(num.get(qn("w:numId")), ilvl)] = fmt

    def prefix(self, para: Paragraph) -> str:
        num_id, ilvl = self._num_pr(para)
        if num_id is None or num_id == "0":
            return ""
        fmt = self.formats.get((num_id, ilvl), "bullet")
        indent = "  " * ilvl
        if fmt in ("bullet", "none"):
            return indent + "- "
        key = (num_id, ilvl)
        self.counters[key] = self.counters.get(key, 0) + 1
        for k in [k for k in self.counters if k[0] == num_id and k[1] > ilvl]:
            del self.counters[k]  # restart deeper levels
        return f"{indent}{self.counters[key]}. "

    @staticmethod
    def _num_pr(para: Paragraph) -> tuple[str | None, int]:
        # Direct numbering first, then numbering inherited from the style chain.
        candidates = [para._p.pPr]
        style = para.style
        while style is not None:
            candidates.append(style.element.pPr)
            style = style.base_style
        for ppr in candidates:
            if ppr is None:
                continue
            num_pr = ppr.find(qn("w:numPr"))
            if num_pr is None:
                continue
            num_id = num_pr.find(qn("w:numId"))
            ilvl = num_pr.find(qn("w:ilvl"))
            return (
                num_id.get(qn("w:val")) if num_id is not None else None,
                int(ilvl.get(qn("w:val"))) if ilvl is not None else 0,
            )
        return None, 0
