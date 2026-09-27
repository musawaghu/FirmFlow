"""What a firm's employees see: the firm's own modules plus the shared AEC baseline.

The baseline is the firm row with is_baseline = true. Its approved modules are
shared by every firm, so each firm's choices about them live in separate rows:
firm_baseline_modules (priority, required, order, hidden) and
firm_baseline_passages (critical for the final check). A confirmed
baseline_overrides row means the firm states a different practice, so the
firm's passage replaces the baseline one: the firm's version wins.

Every employee-facing read (modules list, progress, final check, assistant,
admin progress) goes through firm_content() so they all agree.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db import Repo, Row

PRIORITY_ORDER = {"day_1": 0, "week_1": 1, "later": 2}
# Baseline modules without a firm ordinal sort after the firm's own modules of
# the same priority, so a firm's welcome module stays first.
BASELINE_ORDINAL_OFFSET = 1000


def override_note(firm_name: str) -> str:
    """Shown to employees on a baseline passage the firm overrides. Fixed text, never model output."""
    return f"{firm_name} does this differently."


def baseline_firm_id(repo: Repo) -> str | None:
    firm = repo.select_one("firms", {"is_baseline": True})
    return firm["id"] if firm else None


def module_sort_key(m: Row) -> tuple:
    return (PRIORITY_ORDER.get(m["priority"], 9), m["ordinal"], m["title"])


@dataclass
class Content:
    firm: Row
    modules: list[Row]  # approved and visible, firm settings applied, sorted; each has "layer"
    passages: list[Row]  # effective passages of those modules, in module then passage order

    def module(self, module_id: str) -> Row | None:
        return next((m for m in self.modules if m["id"] == module_id), None)

    def passages_for(self, module_id: str) -> list[Row]:
        return [p for p in self.passages if p["module_id"] == module_id]

    def critical_passages(self) -> list[Row]:
        """Final-check material. Overridden baseline passages never count; the firm's passage does."""
        return [p for p in self.passages if p["is_critical"] and not p["overridden_by_firm"]]


def firm_content(repo: Repo, firm_id: str) -> Content:
    firm = repo.select_one("firms", {"id": firm_id}) or {"id": firm_id, "name": "Your firm"}
    firm_modules = [{**m, "layer": "firm"} for m in repo.select("modules", {"firm_id": firm_id, "status": "approved"})]

    baseline_modules: list[Row] = []
    base_id = baseline_firm_id(repo)
    if base_id and base_id != firm_id:
        settings = {s["module_id"]: s for s in repo.select("firm_baseline_modules", {"firm_id": firm_id})}
        for m in repo.select("modules", {"firm_id": base_id, "status": "approved"}):
            s = settings.get(m["id"], {})
            if s.get("is_hidden"):
                continue
            baseline_modules.append({
                **m,
                "layer": "baseline",
                "priority": s.get("priority") or m["priority"],
                "is_required": m["is_required"] if s.get("is_required") is None else s["is_required"],
                "ordinal": s["ordinal"] if s.get("ordinal") is not None else BASELINE_ORDINAL_OFFSET + m["ordinal"],
            })

    modules = sorted(firm_modules + baseline_modules, key=module_sort_key)
    position = {m["id"]: i for i, m in enumerate(modules)}
    rows = repo.select("module_passages", {"module_id": list(position)})
    rows.sort(key=lambda p: (position[p["module_id"]], p["ordinal"]))

    baseline_ids = {m["id"] for m in baseline_modules}
    critical = {r["passage_id"]: r["is_critical"] for r in repo.select("firm_baseline_passages", {"firm_id": firm_id})}
    # An override only applies while the firm passage is in an approved firm module.
    firm_passages = {p["id"]: p for p in rows if p["module_id"] not in baseline_ids}
    overrides = {
        o["baseline_passage_id"]: firm_passages[o["firm_passage_id"]]
        for o in repo.select("baseline_overrides", {"firm_id": firm_id, "status": "confirmed"})
        if o["firm_passage_id"] in firm_passages
    }

    passages = []
    for p in rows:
        if p["module_id"] not in baseline_ids:
            passages.append({**p, "overridden_by_firm": False, "firm_note": None, "firm_passage_id": None})
        elif (fp := overrides.get(p["id"])) is not None:
            passages.append({
                **p,
                "heading": fp["heading"] or p["heading"],
                "content": fp["content"],
                "kind": fp["kind"],
                "is_critical": False,
                "overridden_by_firm": True,
                "firm_note": override_note(firm["name"]),
                "firm_passage_id": fp["id"],
            })
        else:
            passages.append({
                **p,
                "is_critical": critical.get(p["id"], False),
                "overridden_by_firm": False,
                "firm_note": None,
                "firm_passage_id": None,
            })
    return Content(firm=firm, modules=modules, passages=passages)
