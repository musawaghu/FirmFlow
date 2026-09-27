"""Admin endpoints for uploading, processing, and reviewing onboarding manuals."""

from __future__ import annotations

import logging
import uuid
from pathlib import PurePath
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from app.auth import Profile, require_admin
from app.db import Repo, Row, Storage, get_repo, get_storage
from app.routers.baseline import override_views
from app.schemas import IssueOut, ManualOut, OverrideOut, ReviewOut
from app.services.overrides import OverrideError, refresh_overrides
from app.services.parser import ParseError, parse_manual
from app.services.processing import has_approved_modules, process_manual, save_sections

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/manuals", tags=["manuals"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
FILE_TYPES = {
    ".pdf": ("pdf", "application/pdf", b"%PDF"),
    ".docx": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK"),
}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ProcessRequest(BaseModel):
    module_topics: list[str] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_manual(repo: Repo, profile: Profile, manual_id: str) -> Row:
    try:
        uuid.UUID(manual_id)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Manual not found") from None
    manual = repo.select_one("manuals", {"id": manual_id, "firm_id": profile.firm_id})
    if manual is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Manual not found")
    return manual


def _pages(section: Row) -> str | None:
    start, end = section.get("page_start"), section.get("page_end")
    if start is None:
        return None
    return f"p. {start}" if start == end or end is None else f"pp. {start}-{end}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ManualOut)
def upload_manual(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
    storage: Storage = Depends(get_storage),
):
    """Upload a PDF or DOCX manual. It is parsed right away into source sections."""
    suffix = PurePath(file.filename or "").suffix.lower()
    if suffix not in FILE_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a PDF or DOCX file")
    file_type, content_type, magic = FILE_TYPES[suffix]

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "The file is larger than 25 MB")
    if not data.startswith(magic):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"This doesn't look like a {file_type.upper()} file")

    try:
        parsed = parse_manual(data, file_type)
    except ParseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    manual_id = str(uuid.uuid4())
    path = f"{profile.firm_id}/{manual_id}{suffix}"
    storage.upload(path, data, content_type)
    try:
        manual = repo.insert("manuals", [{
            "id": manual_id,
            "firm_id": profile.firm_id,
            "uploaded_by": profile.id,
            "title": (title or "").strip() or PurePath(file.filename).stem,
            "file_path": path,
            "file_type": file_type,
            "page_count": parsed.page_count,
            "status": "uploaded",
        }])[0]
        save_sections(repo, manual_id, parsed)
    except Exception:
        log.exception("Saving manual %s failed; cleaning up", manual_id)
        try:
            repo.delete("manuals", {"id": manual_id})  # cascades to source_sections
            storage.remove(path)
        except Exception:
            log.exception("Cleanup for manual %s failed", manual_id)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not save the manual") from None
    return manual


@router.get("", response_model=list[ManualOut])
def list_manuals(profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    manuals = repo.select("manuals", {"firm_id": profile.firm_id}, order="created_at")
    return list(reversed(manuals))  # newest first


@router.get("/{manual_id}", response_model=ManualOut)
def get_manual(manual_id: str, profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """Poll this after starting processing; `status` moves to processed or failed."""
    return _get_manual(repo, profile, manual_id)


@router.post("/{manual_id}/process", status_code=status.HTTP_202_ACCEPTED, response_model=ManualOut)
def start_processing(
    manual_id: str,
    background_tasks: BackgroundTasks,
    body: ProcessRequest | None = None,
    force: bool = Query(default=False, description="Restart a run that appears stuck in processing"),
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Enhance the manual into draft modules, flag issues, and run the grounding check.

    Runs in the background. Re-running replaces earlier drafts and issues, so it
    is refused once any module from this manual has been approved.
    """
    manual = _get_manual(repo, profile, manual_id)
    if manual["status"] == "processing" and not force:
        raise HTTPException(status.HTTP_409_CONFLICT, "This manual is already being processed")
    if has_approved_modules(repo, manual_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Modules from this manual are already approved; re-processing would replace them")

    manual = repo.update("manuals", manual_id, {"status": "processing", "error": None})
    topics = [t.strip() for t in (body.module_topics if body and body.module_topics else []) if t.strip()]
    background_tasks.add_task(process_manual, repo, manual, topics or None)
    return manual


@router.get("/{manual_id}/review", response_model=ReviewOut)
def review_manual(manual_id: str, profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """Draft modules with their passages, next to the original source sections."""
    manual = _get_manual(repo, profile, manual_id)
    sections = repo.select("source_sections", {"manual_id": manual_id}, order="ordinal")
    modules = repo.select("modules", {"manual_id": manual_id}, order="ordinal")
    passages = repo.select("module_passages", {"module_id": [m["id"] for m in modules]}, order="ordinal")

    by_module: dict[str, list[Row]] = {}
    for p in passages:
        by_module.setdefault(p["module_id"], []).append(p)
    return {
        "manual": manual,
        "sections": sections,
        "modules": [{**m, "passages": by_module.get(m["id"], [])} for m in modules],
        "overrides": override_views(repo, repo.select("baseline_overrides", {"manual_id": manual_id}, order="created_at")),
    }


@router.get("/{manual_id}/issues", response_model=list[IssueOut])
def list_issues(
    manual_id: str,
    issue_status: Literal["open", "resolved", "dismissed"] | None = Query(default=None, alias="status"),
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Problems flagged in the source: broken links, outdated references, contradictions, missing steps."""
    _get_manual(repo, profile, manual_id)
    filters = {"manual_id": manual_id}
    if issue_status:
        filters["status"] = issue_status
    issues = repo.select("issues", filters, order="created_at")
    section_ids = list({i["source_section_id"] for i in issues if i.get("source_section_id")})
    sections = {s["id"]: s for s in repo.select("source_sections", {"id": section_ids})}

    out = []
    for issue in issues:
        section = sections.get(issue.get("source_section_id"))
        out.append({
            **issue,
            "section_heading": section["heading"] if section else None,
            "pages": _pages(section) if section else None,
        })
    # Keep the manual's reading order.
    return sorted(out, key=lambda i: sections[i["source_section_id"]]["ordinal"] if i.get("source_section_id") in sections else 1 << 30)


@router.get("/{manual_id}/overrides", response_model=list[OverrideOut])
def list_overrides(
    manual_id: str,
    override_status: Literal["proposed", "confirmed", "dismissed"] | None = Query(default=None, alias="status"),
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Where this manual's passages state a different practice than the AEC baseline."""
    _get_manual(repo, profile, manual_id)
    filters = {"manual_id": manual_id}
    if override_status:
        filters["status"] = override_status
    return override_views(repo, repo.select("baseline_overrides", filters, order="created_at"))


@router.post("/{manual_id}/overrides/detect", response_model=list[OverrideOut])
def detect_manual_overrides(manual_id: str, profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """Compare this manual's passages with the AEC baseline again, e.g. after the baseline changed.

    Replaces earlier proposals; confirmed and dismissed overrides keep their decision.
    """
    manual = _get_manual(repo, profile, manual_id)
    if manual["status"] != "processed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Process the manual first")
    try:
        refresh_overrides(repo, manual)
    except OverrideError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Could not compare with the baseline: {exc}") from exc
    return override_views(repo, repo.select("baseline_overrides", {"manual_id": manual_id}, order="created_at"))
