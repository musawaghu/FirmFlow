"""Manual pipeline: upload -> source_sections, then process -> draft modules + issues.

Parsing happens at upload so bad files are rejected immediately and the
original text is reviewable before any AI runs. Processing (enhance + ground)
runs in the background and can be repeated until a module is approved.
"""

from __future__ import annotations

import logging
import uuid

from app.db import Repo, Row
from app.services.enhancer import EnhanceError, enhance_manual
from app.services.grounding import GroundingError, check_enhancement
from app.services.overrides import OverrideError, OverrideResult, refresh_overrides
from app.services.parser import ParsedManual, SourceSection

log = logging.getLogger(__name__)


def save_sections(repo: Repo, manual_id: str, parsed: ParsedManual) -> list[Row]:
    rows = [
        {
            "id": str(uuid.uuid4()),
            "manual_id": manual_id,
            "ordinal": s.ordinal,
            "heading": s.heading,
            "content": s.content,
            "page_start": s.page_start,
            "page_end": s.page_end,
        }
        for s in parsed.sections
    ]
    return repo.insert("source_sections", rows)


def load_sections(repo: Repo, manual_id: str) -> tuple[list[SourceSection], dict[int, str]]:
    """Sections as parser objects, plus ordinal -> source_sections.id."""
    rows = repo.select("source_sections", {"manual_id": manual_id}, order="ordinal")
    sections = [
        SourceSection(r["ordinal"], r["heading"], r["content"], r["page_start"], r["page_end"]) for r in rows
    ]
    return sections, {r["ordinal"]: r["id"] for r in rows}


def clear_outputs(repo: Repo, manual_id: str) -> None:
    """Remove draft modules, passages, issues, and baseline overrides from an earlier run."""
    repo.delete("baseline_overrides", {"manual_id": manual_id})
    module_ids = [m["id"] for m in repo.select("modules", {"manual_id": manual_id})]
    repo.delete("module_passages", {"module_id": module_ids})
    repo.delete("modules", {"manual_id": manual_id})
    repo.delete("issues", {"manual_id": manual_id})


def has_approved_modules(repo: Repo, manual_id: str) -> bool:
    return bool(repo.select("modules", {"manual_id": manual_id, "status": "approved"}))


def process_manual(repo: Repo, manual: Row, module_topics: list[str] | None = None) -> None:
    """Enhance and ground a manual's sections and save the drafts. Runs as a background task."""
    manual_id = manual["id"]
    try:
        clear_outputs(repo, manual_id)
        sections, section_ids = load_sections(repo, manual_id)

        enhancement = enhance_manual(sections, module_topics=module_topics)
        grounding = check_enhancement(enhancement, sections)

        module_rows, passage_rows = [], []
        module_for_section: dict[int, str] = {}
        for mi, module in enumerate(enhancement.modules):
            module_id = str(uuid.uuid4())
            module_rows.append({
                "id": module_id,
                "firm_id": manual["firm_id"],
                "manual_id": manual_id,
                "title": module.title,
                "summary": module.summary,
                "ordinal": mi,
                "priority": module.suggested_priority,
                "status": "draft",
            })
            for pi, p in enumerate(module.passages):
                g = grounding.passages[f"{mi}.{pi}"]
                module_for_section.setdefault(p.source_section_id, module_id)
                passage_rows.append({
                    "id": str(uuid.uuid4()),
                    "module_id": module_id,
                    "source_section_id": section_ids[p.source_section_id],
                    "ordinal": pi,
                    "heading": p.heading,
                    "content": p.content,
                    "kind": p.kind,
                    "grounding_ok": g.grounding_ok,
                    "unsupported_spans": [s.to_json() for s in g.unsupported_spans],
                })

        issue_rows = [
            {
                "id": str(uuid.uuid4()),
                "firm_id": manual["firm_id"],
                "manual_id": manual_id,
                "source_section_id": section_ids[i.source_section_id],
                "related_section_id": section_ids.get(i.related_section_id) if i.related_section_id is not None else None,
                "module_id": module_for_section.get(i.source_section_id),
                "type": i.type,
                "description": i.description,
                "excerpt": i.excerpt,
                "status": "open",
            }
            for i in enhancement.issues
        ]

        repo.insert("modules", module_rows)
        repo.insert("module_passages", passage_rows)
        repo.insert("issues", issue_rows)

        # Not fatal: the drafts are still useful, and the admin can re-run detection.
        try:
            overrides = refresh_overrides(repo, manual)
        except OverrideError as exc:
            overrides = OverrideResult(warnings=[f"Baseline override detection failed: {exc}"])

        repo.update("manuals", manual_id, {
            "status": "processed",
            "error": None,
            "processing_notes": {
                "module_topics": module_topics or [],
                "unused_section_ids": [section_ids[o] for o in enhancement.unused_section_ids],
                "omissions": [{"section_id": section_ids[o.section_id], "text": o.text} for o in grounding.omissions],
                "warnings": enhancement.warnings + grounding.warnings + overrides.warnings,
                "baseline_overrides": len(overrides.overrides),
                "model": enhancement.model,
                "input_tokens": enhancement.input_tokens + grounding.input_tokens + overrides.input_tokens,
                "output_tokens": enhancement.output_tokens + grounding.output_tokens + overrides.output_tokens,
            },
        })
    except (EnhanceError, GroundingError) as exc:
        _fail(repo, manual_id, str(exc))
    except Exception:
        log.exception("Processing manual %s failed", manual_id)
        _fail(repo, manual_id, "Processing failed unexpectedly. Try again, or contact support if it keeps failing.")


def _fail(repo: Repo, manual_id: str, error: str) -> None:
    try:
        clear_outputs(repo, manual_id)
    except Exception:
        log.exception("Could not clear partial output for manual %s", manual_id)
    repo.update("manuals", manual_id, {"status": "failed", "error": error})
