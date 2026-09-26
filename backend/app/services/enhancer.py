"""source_sections -> draft modules + issues.

Claude acts as an editor, not an author: it groups the manual's sections into
modules and rewrites them for clarity, but may not add facts. Problems in the
source (broken links, outdated references, contradictions, missing steps) come
back as issues for the admin instead of being fixed.

The model's output is then checked in code before anything is saved:
passages must cite a real section, issue excerpts must be verbatim quotes
from the section they cite, and sections left out of every module are
reported. The full grounding check (unsupported text inside a passage) lives
in grounding.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from app.services.llm import LLMError, structured_call
from app.services.parser import SourceSection

MAX_TOKENS = 128_000
EFFORT = "high"


class EnhanceError(Exception):
    """The model call failed or returned something unusable."""


# ---------------------------------------------------------------------------
# Model output schema
# ---------------------------------------------------------------------------

class DraftPassage(BaseModel):
    source_section_id: int = Field(description="id of the one source section this passage is drawn from")
    heading: str | None = Field(description="Short heading for the passage, or null")
    kind: Literal["text", "steps", "checklist", "summary"]
    content: str = Field(description="The enhanced passage in markdown")


class DraftModule(BaseModel):
    title: str
    summary: str = Field(description="One or two sentences drawn only from the module's passages")
    suggested_priority: Literal["day_1", "week_1", "later"]
    passages: list[DraftPassage]


class DraftIssue(BaseModel):
    type: Literal["broken_link", "outdated_reference", "contradiction", "missing_step"]
    source_section_id: int = Field(description="id of the section containing the excerpt")
    excerpt: str = Field(description="Exact quote from that section showing the problem")
    related_section_id: int | None = Field(description="For contradictions: id of the conflicting section, else null")
    description: str = Field(
        description="What is wrong, for the admin. Name sections by heading, never by id. Do not propose a corrected value."
    )


class Enhancement(BaseModel):
    modules: list[DraftModule]
    issues: list[DraftIssue]


# ---------------------------------------------------------------------------
# Result returned to callers
# ---------------------------------------------------------------------------

@dataclass
class EnhancementResult:
    modules: list[DraftModule]
    issues: list[DraftIssue]
    unused_section_ids: list[int]  # sections that appear in no module, for admin review
    warnings: list[str] = field(default_factory=list)  # model output dropped by validation
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are the editor for FIRM FLOW, an onboarding platform for architecture firms. \
A firm has uploaded its existing onboarding manual, split into numbered source \
sections. Turn it into clear onboarding modules for new hires (interns, designers, \
architects), and report problems in the source to the firm's admin.

The firm's promise to its employees is that FIRM FLOW never invents anything. \
Every sentence a new hire reads must be supported by the source section it cites. \
An admin reviews each module side by side with the original before anyone sees it.

## What you may do
- Group and reorder sections into modules. Several sections can feed one module.
- Rewrite for clarity: plain language, short sentences, second person ("you").
- Turn procedures into numbered steps and lists of requirements into checklists.
- Add short headings and summaries, drawn only from the text.
- Split one section into several passages (for example, a text passage and a steps \
passage). Each passage draws from exactly one section.
- Leave out a section with no onboarding value (for example, a social note). It is \
listed for the admin automatically; don't mention it.

## What you must not do
- Add any fact, number, date, deadline, name, title, email, link, file path, \
software version, or policy that is not in the cited section. Do not use general \
knowledge about architecture, Revit, HR law, or how firms usually work.
- Drop a fact, number, name, link, or path from a section you use. Keep them \
exactly as written, including links and versions you are flagging.
- Resolve a problem. When two sections contradict each other, keep each statement \
in the passage drawn from its own section and report the contradiction; do not \
pick one. When a procedure is missing a step, do not write the step, and do not \
renumber the steps to hide the gap. Keep a broken or outdated link as written and \
report it.

## Issues to report
- broken_link: a link, file path, or reference that the manual itself shows is \
dead, retired, moved, or a placeholder (for example "TBD" or "old link"), or that \
is inconsistent with the manual's other references (for example a file path on a \
server that no other path in the manual uses).
- outdated_reference: software, systems, versions, or materials the manual itself \
shows are superseded, or that are clearly obsolete (for example an old software \
version when the manual names a newer one).
- contradiction: two statements that cannot both be true (deadlines, amounts, \
hours, frequencies, versions). Cite one section in source_section_id and the other \
in related_section_id; they may be the same section.
- missing_step: a procedure that skips a number or leaves out an action needed to \
finish it.
Report each distinct problem once. The excerpt must be copied exactly from the \
cited section. The description tells the admin what is wrong and where; it must \
not propose the correct value. Section ids are internal and the admin never sees \
them, so never write "section 21" in a description. Name a section by its heading \
instead (for example "the Timesheets section" or "the PTO FAQ").

## Priorities
Suggest a priority for each module; the admin makes the final call.
- day_1: needed in the first day to work safely and correctly (for example \
timesheets, model-handling rules, conduct and reporting policies).
- week_1: needed within the first week.
- later: useful background.
"""


def _render_sections(sections: list[SourceSection]) -> str:
    parts = []
    for s in sections:
        pages = f"{s.page_start}" if s.page_start == s.page_end else f"{s.page_start}-{s.page_end}"
        heading = s.heading or "(no heading)"
        parts.append(
            f'<section id="{s.ordinal}" pages="{pages}">\n'
            f"<heading>{heading}</heading>\n"
            f"{s.content}\n"
            f"</section>"
        )
    return "\n\n".join(parts)


def _user_prompt(sections: list[SourceSection], module_topics: list[str] | None) -> str:
    prompt = f"<manual>\n{_render_sections(sections)}\n</manual>\n\n"
    if module_topics:
        topics = "\n".join(f"- {t}" for t in module_topics)
        prompt += (
            "The admin wants these modules, in this order. A topic may be followed by a colon "
            "and what the module should cover; use only the part before the colon as the "
            "module title. Put each section's content in the module where it fits best. "
            "Content that fits none of them can go in additional modules after these, or be "
            "left out if it has no onboarding value.\n"
            f"{topics}\n\n"
        )
    prompt += "Produce the modules and issues."
    return prompt


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def enhance_manual(
    sections: list[SourceSection],
    *,
    module_topics: list[str] | None = None,
    client: anthropic.Anthropic | None = None,
    model: str | None = None,
) -> EnhancementResult:
    """Propose draft modules and issues for a parsed manual.

    Passages and issues refer to sections by `SourceSection.ordinal`; the caller
    maps ordinals to source_sections rows when saving.
    """
    if not sections:
        raise EnhanceError("The manual has no sections")

    try:
        enhancement, message = structured_call(
            system=SYSTEM_PROMPT,
            user=_user_prompt(sections, module_topics),
            output_format=Enhancement,
            max_tokens=MAX_TOKENS,
            effort=EFFORT,
            client=client,
            model=model,
        )
    except LLMError as exc:
        raise EnhanceError(str(exc)) from exc

    result = validate(enhancement, sections)
    result.model = message.model
    result.input_tokens = message.usage.input_tokens
    result.output_tokens = message.usage.output_tokens
    return result


# ---------------------------------------------------------------------------
# Deterministic checks on the model output
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Loose form for quote matching: case, whitespace, quote style, markdown bullets."""
    text = text.lower()
    text = re.sub(r"[‘’‚′]", "'", text)
    text = re.sub(r"[“”„″]", '"', text)
    text = re.sub(r"[–—]", "-", text)
    text = re.sub(r"(^|\n)\s*(- |\d+\.\s+)", " ", text)
    return re.sub(r"\s+", " ", text).strip().strip("\"'")


def validate(enhancement: Enhancement, sections: list[SourceSection]) -> EnhancementResult:
    """Drop output that cites nonexistent sections or misquotes them."""
    by_id = {s.ordinal: s for s in sections}
    warnings: list[str] = []

    modules = []
    for module in enhancement.modules:
        passages = []
        for p in module.passages:
            if p.source_section_id not in by_id:
                warnings.append(f"Dropped a passage in '{module.title}': it cites section {p.source_section_id}, which does not exist")
            elif not p.content.strip():
                warnings.append(f"Dropped an empty passage in '{module.title}'")
            else:
                passages.append(p)
        if passages:
            modules.append(module.model_copy(update={"passages": passages}))
        else:
            warnings.append(f"Dropped module '{module.title}': no valid passages")

    issues = []
    seen = set()
    for issue in enhancement.issues:
        source = by_id.get(issue.source_section_id)
        if source is None:
            warnings.append(f"Dropped a {issue.type} issue: it cites section {issue.source_section_id}, which does not exist")
            continue
        if _normalize(issue.excerpt) not in _normalize(source.content):
            warnings.append(f"Dropped a {issue.type} issue: its excerpt is not in section {issue.source_section_id}: {issue.excerpt!r}")
            continue
        if issue.related_section_id is not None and issue.related_section_id not in by_id:
            issue = issue.model_copy(update={"related_section_id": None})
        key = (issue.type, issue.source_section_id, _normalize(issue.excerpt))
        if key in seen:
            continue
        seen.add(key)
        issues.append(issue)

    used = {p.source_section_id for m in modules for p in m.passages}
    unused = [s.ordinal for s in sections if s.ordinal not in used]

    return EnhancementResult(modules=modules, issues=issues, unused_section_ids=unused, warnings=warnings)
