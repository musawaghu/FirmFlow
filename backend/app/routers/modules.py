"""Module review (admin) and module viewing and progress (employees)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from app.auth import Profile, get_current_profile, require_admin
from app.db import Repo, Row, get_repo
from app.schemas import ModuleListOut, ModuleOut, PassageEditOut, ProgressOut
from app.services.grounding import GroundingError, PassageInput, check_passages
from app.services.parser import SourceSection
from app.services.progress import final_check_unlocked, load_progress, required_progress

router = APIRouter(prefix="/api/modules", tags=["modules"])
passages_router = APIRouter(prefix="/api/passages", tags=["modules"])

PRIORITY_ORDER = {"day_1": 0, "week_1": 1, "later": 2}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ModuleUpdate(BaseModel):
    status: Literal["draft", "approved", "rejected"] | None = None
    priority: Literal["day_1", "week_1", "later"] | None = None
    is_required: bool | None = None
    ordinal: int | None = None
    title: str | None = None
    summary: str | None = None
    # Approve even though some passages failed or skipped the grounding check,
    # after the admin has confirmed the flags are false positives.
    confirm_flagged: bool = False

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title can't be blank")
        return v.strip() if v else v


class PassageUpdate(BaseModel):
    content: str | None = None
    heading: str | None = None
    kind: Literal["text", "steps", "checklist", "summary"] | None = None
    is_critical: bool | None = None

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Content can't be blank")
        return v


class ProgressUpdate(BaseModel):
    status: Literal["in_progress", "completed"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def _get_module(repo: Repo, profile: Profile, module_id: str, approved_only: bool = False) -> Row:
    filters = {"id": module_id, "firm_id": profile.firm_id}
    if approved_only:
        filters["status"] = "approved"
    module = repo.select_one("modules", filters) if _valid_uuid(module_id) else None
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module not found")
    return module


def _with_passages(repo: Repo, module: Row) -> Row:
    return {**module, "passages": repo.select("module_passages", {"module_id": module["id"]}, order="ordinal")}


# ---------------------------------------------------------------------------
# Admin: review modules and passages
# ---------------------------------------------------------------------------

@router.patch("/{module_id}", response_model=ModuleOut)
def update_module(
    module_id: str,
    body: ModuleUpdate,
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Approve, reject, or return a module to draft; set priority and order; edit title and summary.

    Approval requires every passage to have passed the grounding check, unless
    `confirm_flagged` is set. Title and summary edits need the module in draft.
    """
    module = _get_module(repo, profile, module_id)
    changes: Row = {}

    edits_content = body.title is not None or body.summary is not None
    if edits_content and module["status"] == "approved" and body.status != "draft":
        raise HTTPException(status.HTTP_409_CONFLICT, "Move the module back to draft before editing it")
    if body.title is not None:
        changes["title"] = body.title
    if body.summary is not None:
        changes["summary"] = body.summary.strip() or None
    for field in ("priority", "is_required", "ordinal"):
        if getattr(body, field) is not None:
            changes[field] = getattr(body, field)

    if body.status == "approved" and module["status"] != "approved":
        passages = repo.select("module_passages", {"module_id": module_id})
        if not passages:
            raise HTTPException(status.HTTP_409_CONFLICT, "A module needs at least one passage to be approved")
        flagged = [p["id"] for p in passages if p.get("grounding_ok") is not True]
        if flagged and not body.confirm_flagged:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                {
                    "message": "Some passages have unsupported text or haven't been checked. "
                    "Edit them, or confirm the flags are false positives with confirm_flagged.",
                    "passage_ids": flagged,
                },
            )
    if body.status is not None and body.status != module["status"]:
        changes["status"] = body.status
        reviewed = body.status in ("approved", "rejected")
        changes["reviewed_by"] = profile.id if reviewed else None
        changes["reviewed_at"] = _now() if reviewed else None

    if changes:
        changes["updated_at"] = _now()
        module = repo.update("modules", module_id, changes)
    return _with_passages(repo, module)


@passages_router.patch("/{passage_id}", response_model=PassageEditOut)
def update_passage(
    passage_id: str,
    body: PassageUpdate,
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Edit a passage or mark it critical for the final check.

    Changing the text or heading re-runs the grounding check against the
    passage's source section.
    """
    passage = repo.select_one("module_passages", {"id": passage_id}) if _valid_uuid(passage_id) else None
    module = repo.select_one("modules", {"id": passage["module_id"], "firm_id": profile.firm_id}) if passage else None
    if passage is None or module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Passage not found")

    sent = body.model_fields_set
    changes: Row = {}
    if "content" in sent and body.content is not None and body.content != passage["content"]:
        changes["content"] = body.content
    heading = (body.heading or "").strip() or None
    if "heading" in sent and heading != passage["heading"]:
        changes["heading"] = heading
    if body.kind is not None and body.kind != passage["kind"]:
        changes["kind"] = body.kind
    if changes and module["status"] == "approved":
        raise HTTPException(status.HTTP_409_CONFLICT, "Move the module back to draft before editing it")
    if body.is_critical is not None:
        changes["is_critical"] = body.is_critical

    grounding_error = None
    if "content" in changes or "heading" in changes:
        section = repo.select_one("source_sections", {"id": passage["source_section_id"]})
        source = SourceSection(section["ordinal"], section["heading"], section["content"], section["page_start"], section["page_end"])
        edited = PassageInput(
            key=passage_id,
            heading=changes.get("heading", passage["heading"]),
            content=changes.get("content", passage["content"]),
            source=source,
        )
        try:
            result = check_passages([edited]).passages[passage_id]
            changes["grounding_ok"] = result.grounding_ok
            changes["unsupported_spans"] = [s.to_json() for s in result.unsupported_spans]
        except GroundingError as exc:
            # Save the edit, but mark it unchecked so it can't be approved unnoticed.
            grounding_error = str(exc)
            changes["grounding_ok"] = None
            changes["unsupported_spans"] = []

    if changes:
        passage = repo.update("module_passages", passage_id, changes)
        repo.update("modules", module["id"], {"updated_at": _now()})
    return {**passage, "grounding_error": grounding_error}


# ---------------------------------------------------------------------------
# Employees: approved modules and progress
# ---------------------------------------------------------------------------

@router.get("", response_model=ModuleListOut)
def list_modules(profile: Profile = Depends(get_current_profile), repo: Repo = Depends(get_repo)):
    """Approved modules, Day 1 first, with the caller's own progress."""
    modules, progress = load_progress(repo, profile.firm_id, profile.id)
    modules.sort(key=lambda m: (PRIORITY_ORDER.get(m["priority"], 9), m["ordinal"], m["title"]))
    passages = repo.select("module_passages", {"module_id": [m["id"] for m in modules]}, order="ordinal")

    by_module: dict[str, list[Row]] = {}
    for p in passages:
        by_module.setdefault(p["module_id"], []).append(p)
    out = [
        {**m, "progress": progress.get(m["id"], "not_started"), "passages": by_module.get(m["id"], [])}
        for m in modules
    ]
    required, completed = required_progress(modules, progress)
    return {
        "full_name": profile.full_name,
        "required_modules": required,
        "completed_required": completed,
        "final_check_unlocked": final_check_unlocked(required, completed),
        "modules": out,
    }


@router.post("/{module_id}/progress", response_model=ProgressOut)
def update_progress(
    module_id: str,
    body: ProgressUpdate,
    profile: Profile = Depends(get_current_profile),
    repo: Repo = Depends(get_repo),
):
    """Mark an approved module started or completed. Completed modules stay completed."""
    _get_module(repo, profile, module_id, approved_only=True)
    now = _now()
    existing = repo.select_one("module_progress", {"profile_id": profile.id, "module_id": module_id})

    if existing is None:
        return repo.insert("module_progress", [{
            "profile_id": profile.id,
            "module_id": module_id,
            "status": body.status,
            "started_at": now,
            "completed_at": now if body.status == "completed" else None,
        }])[0]
    if existing["status"] == "completed" or existing["status"] == body.status:
        return existing
    changes = {"status": body.status, "started_at": existing.get("started_at") or now}
    if body.status == "completed":
        changes["completed_at"] = now
    return repo.update("module_progress", existing["id"], changes)
