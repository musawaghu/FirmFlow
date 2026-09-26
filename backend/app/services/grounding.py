"""Checks enhanced passages against the source sections they cite.

Two layers:

1. Rules (no model call): every number, time, URL, email, file path, and
   go-link in a passage must appear in its source section. These are the
   inventions that hurt most (a wrong deadline, extension, or link), and a
   string check catches them reliably.
2. Model: Claude reads each passage next to its source and quotes any text
   that is not supported: added policies, changed obligations, a silently
   resolved contradiction, invented steps.

Every unsupported span quotes the passage exactly so the admin UI can
highlight it in red. The rules also run in the other direction and report
facts from a source section that no passage citing it kept (omissions).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import anthropic
from pydantic import BaseModel, Field

from app.services.enhancer import EnhancementResult
from app.services.llm import LLMError, structured_call
from app.services.parser import SourceSection

MAX_TOKENS = 64_000
EFFORT = "high"
BATCH_SIZE = 40  # passages per model call


class GroundingError(Exception):
    """The model check failed."""


@dataclass
class PassageInput:
    key: str  # caller's identifier, e.g. a module_passages id
    heading: str | None
    content: str
    source: SourceSection


@dataclass
class UnsupportedSpan:
    text: str  # exact text from the passage heading or content, when located
    reason: str
    check: str  # "rule" or "model"
    located: bool = True  # False when the model's quote couldn't be found in the passage

    def to_json(self) -> dict:
        return {"text": self.text, "reason": self.reason, "check": self.check, "located": self.located}


@dataclass
class PassageGrounding:
    key: str
    unsupported_spans: list[UnsupportedSpan] = field(default_factory=list)

    @property
    def grounding_ok(self) -> bool:
        return not self.unsupported_spans


@dataclass
class Omission:
    section_id: int
    text: str  # a number, link, email, or path from the source that no citing passage kept


@dataclass
class GroundingResult:
    passages: dict[str, PassageGrounding]
    omissions: list[Omission]
    warnings: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def flagged(self) -> list[PassageGrounding]:
        return [p for p in self.passages.values() if not p.grounding_ok]


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def check_passages(
    passages: list[PassageInput],
    *,
    use_model: bool = True,
    client: anthropic.Anthropic | None = None,
    model: str | None = None,
) -> GroundingResult:
    """Check passages against their sources. Use for new drafts and after admin edits."""
    result = GroundingResult(passages={p.key: PassageGrounding(p.key) for p in passages}, omissions=[])

    for p in passages:
        result.passages[p.key].unsupported_spans.extend(rule_spans(p))
    result.omissions = find_omissions(passages)

    if use_model and passages:
        for start in range(0, len(passages), BATCH_SIZE):
            _model_check(passages[start:start + BATCH_SIZE], result, client=client, model=model)

    return result


def check_enhancement(
    enhancement: EnhancementResult,
    sections: list[SourceSection],
    **kwargs,
) -> GroundingResult:
    """Check an enhancer result. Passage keys are "<module index>.<passage index>"."""
    by_id = {s.ordinal: s for s in sections}
    passages = [
        PassageInput(key=f"{mi}.{pi}", heading=p.heading, content=p.content, source=by_id[p.source_section_id])
        for mi, module in enumerate(enhancement.modules)
        for pi, p in enumerate(module.passages)
    ]
    return check_passages(passages, **kwargs)


# ---------------------------------------------------------------------------
# Rule check
# ---------------------------------------------------------------------------

URL_RE = re.compile(r"https?://[^\s<>()\[\]\"'`]+")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
UNC_RE = re.compile(r"\\\\[^\s`]+")
DRIVE_RE = re.compile(r"\b[A-Za-z]:\\[^\s`]*")
GOLINK_RE = re.compile(r"\bgo/[\w-]+")
NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:[.,:]\d+)*")
LIST_MARKER_RE = re.compile(r"^(\s*)\d+[.)]\s", re.MULTILINE)
TRAILING_PUNCT = ".,;:!?)"

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "ninety": 90, "hundred": 100,
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "noon": 12, "midnight": 12,
}
NUMBER_WORD_RE = re.compile(r"\b(" + "|".join(NUMBER_WORDS) + r")\b", re.IGNORECASE)

LINK_PATTERNS = [
    (URL_RE, "link"),
    (EMAIL_RE, "email address"),
    (UNC_RE, "file path"),
    (DRIVE_RE, "file path"),
    (GOLINK_RE, "link"),
]


@dataclass
class _Tokens:
    links: list[tuple[str, str]]  # (exact text, kind)
    numbers: list[str]  # exact text


def _tokens(text: str) -> _Tokens:
    links = []
    for pattern, kind in LINK_PATTERNS:
        for m in pattern.finditer(text):
            token = m.group().rstrip(TRAILING_PUNCT)
            if token and not any(token in existing for existing, _ in links):
                links.append((token, kind))
    # Numbers inside links are covered by the link check; list markers aren't facts.
    rest = text
    for token, _ in links:
        rest = rest.replace(token, " ")
    rest = LIST_MARKER_RE.sub(r"\1", rest)
    return _Tokens(links=links, numbers=[m.group() for m in NUMBER_RE.finditer(rest)])


def _number_forms(text: str) -> set[str]:
    """Every numeric value mentioned in text: numerals, their parts (5:00 -> 5), and number words."""
    tokens = _tokens(text)
    forms = set()
    for n in tokens.numbers:
        n = n.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", n) else n
        forms.add(n)
        forms.update(_parts(n))
    forms.update(str(NUMBER_WORDS[w.lower()]) for w in NUMBER_WORD_RE.findall(text))
    return forms


def _parts(number: str) -> list[str]:
    """Components of 5:00 or 1.5, ignoring zero-only parts and leading zeros."""
    return [p.lstrip("0") or "0" for p in re.split(r"[.,:]", number) if p.strip("0")]


def _number_supported(number: str, forms: set[str]) -> bool:
    plain = number.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", number) else number
    if plain in forms or number in forms:
        return True
    parts = _parts(plain)
    return bool(parts) and all(p in forms for p in parts)


def _link_supported(token: str, text: str) -> bool:
    return token.lower() in text.lower()


def rule_spans(p: PassageInput) -> list[UnsupportedSpan]:
    """Numbers and links in the passage that its source (heading or content) doesn't contain."""
    source = f"{p.source.heading or ''}\n{p.source.content}"
    # Heading numbers ("4.2") support only themselves, not their parts, so a
    # section number can't vouch for an invented "2 days".
    forms = _number_forms(p.source.content) | set(_tokens(p.source.heading or "").numbers)
    spans: list[UnsupportedSpan] = []
    seen = set()
    for part in (p.heading or "", p.content):
        tokens = _tokens(part)
        for token, kind in tokens.links:
            if token not in seen and not _link_supported(token, source):
                seen.add(token)
                spans.append(UnsupportedSpan(token, f"This {kind} is not in the source section.", "rule"))
        for number in tokens.numbers:
            if number not in seen and not _number_supported(number, forms):
                seen.add(number)
                spans.append(UnsupportedSpan(number, "This number is not in the source section.", "rule"))
    return spans


def find_omissions(passages: list[PassageInput]) -> list[Omission]:
    """Numbers and links in a source section that no passage citing it kept."""
    by_section: dict[int, tuple[SourceSection, list[str]]] = {}
    for p in passages:
        entry = by_section.setdefault(p.source.ordinal, (p.source, []))
        entry[1].append(f"{p.heading or ''}\n{p.content}")

    omissions = []
    for section_id, (section, texts) in sorted(by_section.items()):
        combined = "\n".join(texts)
        forms = _number_forms(combined)
        tokens = _tokens(section.content)
        for token, _ in tokens.links:
            if not _link_supported(token, combined):
                omissions.append(Omission(section_id, token))
        for number in dict.fromkeys(tokens.numbers):
            if not _number_supported(number, forms):
                omissions.append(Omission(section_id, number))
    return omissions


# ---------------------------------------------------------------------------
# Model check
# ---------------------------------------------------------------------------

class ModelSpan(BaseModel):
    passage_id: str
    text: str = Field(description="Shortest exact quote from the passage heading or content")
    reason: str = Field(description="What the source does or doesn't say, in one sentence")


class ModelGrounding(BaseModel):
    unsupported: list[ModelSpan]


SYSTEM_PROMPT = """\
You check onboarding passages against the manual sections they were written from. \
FIRM FLOW promises new hires at architecture firms that nothing in their onboarding \
is invented. The firm's admin sees every span you report highlighted in red before \
approving the module.

For each passage, report every part that its cited source section does not support:
- facts, numbers, dates, times, names, titles, contacts, links, paths, software, or \
versions that are not in the source
- policies, requirements, permissions, or consequences that are not in the source
- changed meaning: a stronger or weaker obligation (may becomes must), or a \
different condition, scope, person, or time
- a contradiction in the source that the passage silently resolves by keeping only one side
- steps or actions the source doesn't contain

These are fine and must not be reported: paraphrase and plain-language rewording, \
reordering, formatting as steps or checklists, headings and summaries that only \
restate the source, and neutral connecting phrases ("Here's how", "Before you start").

Judge only against the cited section. Text that is true in general but absent from \
the section is unsupported. Quote the shortest span that carries the unsupported \
claim, copied character for character from the passage heading or content. Report \
nothing for a fully supported passage.
"""


def _user_prompt(batch: list[PassageInput], ids: list[str]) -> str:
    sources = {p.source.ordinal: p.source for p in batch}
    source_xml = "\n\n".join(
        f'<section id="{s.ordinal}">\n<heading>{s.heading or "(no heading)"}</heading>\n{s.content}\n</section>'
        for s in sources.values()
    )
    passage_xml = "\n\n".join(
        f'<passage id="{pid}" source="{p.source.ordinal}">\n'
        f"<heading>{p.heading or ''}</heading>\n<content>\n{p.content}\n</content>\n</passage>"
        for pid, p in zip(ids, batch)
    )
    return (
        f"<sources>\n{source_xml}\n</sources>\n\n<passages>\n{passage_xml}\n</passages>\n\n"
        "Report the unsupported spans."
    )


def _locate(quote: str, p: PassageInput) -> str | None:
    """Find the model's quote in the passage, tolerating case and whitespace differences."""
    for text in (p.content, p.heading or ""):
        if quote in text:
            return quote
    words = quote.split()
    if not words:
        return None
    pattern = re.compile(r"\s+".join(re.escape(w) for w in words), re.IGNORECASE)
    for text in (p.content, p.heading or ""):
        if m := pattern.search(text):
            return m.group()
    return None


def _model_check(batch, result: GroundingResult, *, client, model) -> None:
    ids = [f"P{i + 1}" for i in range(len(batch))]
    by_id = dict(zip(ids, batch))
    try:
        output, message = structured_call(
            system=SYSTEM_PROMPT,
            user=_user_prompt(batch, ids),
            output_format=ModelGrounding,
            max_tokens=MAX_TOKENS,
            effort=EFFORT,
            client=client,
            model=model,
        )
    except LLMError as exc:
        raise GroundingError(str(exc)) from exc

    result.input_tokens += message.usage.input_tokens
    result.output_tokens += message.usage.output_tokens

    for span in output.unsupported:
        p = by_id.get(span.passage_id)
        if p is None:
            result.warnings.append(f"The model reported an unknown passage {span.passage_id!r}")
            continue
        grounding = result.passages[p.key]
        located = _locate(span.text, p)
        # Keep unlocated reports too: a real problem with a sloppy quote still
        # needs the admin's eyes, it just can't be highlighted.
        text = located or span.text
        if any(s.text.lower() == text.lower() for s in grounding.unsupported_spans):
            continue
        grounding.unsupported_spans.append(UnsupportedSpan(text, span.reason, "model", located=located is not None))
