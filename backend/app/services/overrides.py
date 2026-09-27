"""Firm overrides of the AEC baseline: where the firm's own rule wins.

Claude compares a firm's passages with the approved baseline passages and
proposes an override wherever the firm states a different practice on the same
topic ("we number sheets A-101", baseline: "A1.01"). Each proposal must quote
both passages verbatim; proposals whose quotes can't be found are dropped. The
firm's admin confirms or dismisses every proposal before employees see the
firm's version in place of the baseline one.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import anthropic
from pydantic import BaseModel, Field

from app.db import Repo, Row
from app.services.content import baseline_firm_id
from app.services.llm import LLMError, structured_call
from app.services.quotes import locate_quote

MAX_TOKENS = 32_000
EFFORT = "high"
DEADLINE = 300.0  # seconds


class OverrideError(Exception):
    """The model call failed."""


# ---------------------------------------------------------------------------
# Model output schema
# ---------------------------------------------------------------------------

class ProposedOverride(BaseModel):
    firm_passage_id: str = Field(description="id of the firm passage, e.g. F3")
    baseline_passage_id: str = Field(description="id of the baseline passage it overrides, e.g. B2")
    firm_excerpt: str = Field(description="Shortest exact quote from the firm passage that states the firm's practice")
    baseline_excerpt: str = Field(description="Shortest exact quote from the baseline passage that the firm's practice replaces")
    difference: str = Field(description="One sentence for the firm's admin: what the baseline says and what the firm does instead")


class OverrideSet(BaseModel):
    overrides: list[ProposedOverride]


# ---------------------------------------------------------------------------
# Inputs and results
# ---------------------------------------------------------------------------

@dataclass
class PassageText:
    key: str  # module_passages.id
    module_title: str
    heading: str | None
    content: str


@dataclass
class Override:
    firm_passage_key: str
    baseline_passage_key: str
    firm_excerpt: str
    baseline_excerpt: str
    difference: str


@dataclass
class OverrideResult:
    overrides: list[Override] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
FIRM FLOW onboards new hires at architecture firms with two layers of content: an \
AEC baseline shared by every firm (general practice such as Revit worksharing, file \
naming, drawing sets, consultant coordination) and each firm's own passages. Where \
they conflict, the firm's version wins: new hires see the firm's passage in place \
of the baseline one.

Find every place where a firm passage overrides a baseline passage. An override \
means both passages address the same practice and the firm's instruction differs, \
so following the baseline would break the firm's rule. For example, a different \
naming or numbering format, a different location or tool, a different procedure, \
requirement, frequency, or responsible role.

These are not overrides and must not be reported:
- The firm adds specifics the baseline leaves open (the baseline says "your firm's \
file server", the firm names the server).
- The firm covers a topic the baseline doesn't, or the baseline covers one the firm doesn't.
- Both say the same thing in different words.

For each override, quote the shortest span that states the practice from each \
passage, copied character for character, and write one sentence for the firm's \
admin saying what the baseline says and what the firm does instead. Report \
nothing if there are no overrides.
"""


def _render(label: str, ids: list[str], passages: list[PassageText]) -> str:
    parts = []
    for pid, p in zip(ids, passages):
        parts.append(
            f'<passage id="{pid}" module="{p.module_title}">\n'
            f"<heading>{p.heading or ''}</heading>\n<content>\n{p.content}\n</content>\n</passage>"
        )
    return f"<{label}>\n" + "\n\n".join(parts) + f"\n</{label}>"


def _user_prompt(firm_ids, firm, baseline_ids, baseline) -> str:
    return (
        _render("baseline_passages", baseline_ids, baseline)
        + "\n\n"
        + _render("firm_passages", firm_ids, firm)
        + "\n\nReport the firm passages that override baseline passages."
    )


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def detect_overrides(
    firm: list[PassageText],
    baseline: list[PassageText],
    *,
    client: anthropic.Anthropic | None = None,
    model: str | None = None,
) -> OverrideResult:
    """Propose firm overrides of baseline passages, keeping only those whose quotes check out."""
    result = OverrideResult()
    if not firm or not baseline:
        return result

    firm_ids = [f"F{i + 1}" for i in range(len(firm))]
    baseline_ids = [f"B{i + 1}" for i in range(len(baseline))]
    firm_by_id, baseline_by_id = dict(zip(firm_ids, firm)), dict(zip(baseline_ids, baseline))
    try:
        output, message = structured_call(
            system=SYSTEM_PROMPT,
            user=_user_prompt(firm_ids, firm, baseline_ids, baseline),
            output_format=OverrideSet,
            max_tokens=MAX_TOKENS,
            effort=EFFORT,
            client=client,
            model=model,
            deadline=DEADLINE,
        )
    except LLMError as exc:
        raise OverrideError(str(exc)) from exc
    result.input_tokens = message.usage.input_tokens
    result.output_tokens = message.usage.output_tokens

    seen = set()
    for o in output.overrides:
        fp, bp = firm_by_id.get(o.firm_passage_id), baseline_by_id.get(o.baseline_passage_id)
        if fp is None or bp is None:
            result.warnings.append(f"Dropped an override citing unknown passages {o.firm_passage_id!r} / {o.baseline_passage_id!r}")
            continue
        firm_quote = locate_quote(o.firm_excerpt, fp.content, fp.heading or "")
        baseline_quote = locate_quote(o.baseline_excerpt, bp.content, bp.heading or "")
        if firm_quote is None or baseline_quote is None:
            result.warnings.append(f"Dropped an override whose quotes aren't in the passages: {o.difference}")
            continue
        if (fp.key, bp.key) in seen:
            continue
        seen.add((fp.key, bp.key))
        result.overrides.append(Override(fp.key, bp.key, firm_quote, baseline_quote, o.difference.strip()))
    return result


def refresh_overrides(
    repo: Repo,
    manual: Row,
    *,
    client: anthropic.Anthropic | None = None,
    model: str | None = None,
) -> OverrideResult:
    """Re-detect overrides for a firm manual's passages and save them as proposals.

    Replaces earlier proposals; a pair the admin already confirmed or dismissed
    keeps its decision. Does nothing for the baseline itself or before the
    baseline has approved modules.
    """
    base_id = baseline_firm_id(repo)
    if base_id is None or manual["firm_id"] == base_id:
        return OverrideResult()

    firm_modules = {m["id"]: m for m in repo.select("modules", {"manual_id": manual["id"]}) if m["status"] != "rejected"}
    baseline_modules = {m["id"]: m for m in repo.select("modules", {"firm_id": base_id, "status": "approved"})}
    firm_rows = repo.select("module_passages", {"module_id": list(firm_modules)}, order="ordinal")
    baseline_rows = repo.select("module_passages", {"module_id": list(baseline_modules)}, order="ordinal")

    def texts(rows, modules):
        return [PassageText(r["id"], modules[r["module_id"]]["title"], r["heading"], r["content"]) for r in rows]

    result = detect_overrides(texts(firm_rows, firm_modules), texts(baseline_rows, baseline_modules), client=client, model=model)

    repo.delete("baseline_overrides", {"manual_id": manual["id"], "status": "proposed"})
    decided = {
        (o["firm_passage_id"], o["baseline_passage_id"])
        for o in repo.select("baseline_overrides", {"manual_id": manual["id"]})
    }
    repo.insert("baseline_overrides", [
        {
            "id": str(uuid.uuid4()),
            "firm_id": manual["firm_id"],
            "manual_id": manual["id"],
            "firm_passage_id": o.firm_passage_key,
            "baseline_passage_id": o.baseline_passage_key,
            "firm_excerpt": o.firm_excerpt,
            "baseline_excerpt": o.baseline_excerpt,
            "difference": o.difference,
            "status": "proposed",
        }
        for o in result.overrides
        if (o.firm_passage_key, o.baseline_passage_key) not in decided
    ])
    return result
