"""Admin endpoints for the shared AEC baseline: this firm's settings and overrides.

Baseline modules are shared by every firm and can't be edited here. A firm
chooses which ones its employees see, their priority and order, and which
baseline passages are critical for its final check. Where the firm's own manual
states a different practice, a confirmed override shows the firm's version.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import Profile, require_admin
from app.db import Repo, Row, get_repo
from app.schemas import BaselineModuleOut, OverrideOut
from app.services.content import BASELINE_ORDINAL_OFFSET, baseline_firm_id, module_sort_key

router = APIRouter(prefix="/api", tags=["baseline"])


class BaselineModuleUpdate(BaseModel):
    priority: Literal["day_1", "week_1", "later"] | None = None
    is_required: bool | None = None
    ordinal: int | None = None
    is_hidden: bool | None = None


class OverrideUpdate(BaseModel):
    status: Literal["proposed", "confirmed", "dismissed"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def override_views(repo: Repo, overrides: list[Row]) -> list[dict]:
    """Overrides with both passages named, for the admin."""
    passage_ids = list({o[k] for o in overrides for k in ("firm_passage_id", "baseline_passage_id")})
    passages = {p["id"]: p for p in repo.select("module_passages", {"id": passage_ids})}
    modules = {m["id"]: m for m in repo.select("modules", {"id": list({p["module_id"] for p in passages.values()})})}

    def ref(passage_id: str) -> dict:
        p = passages[passage_id]
        return {"passage_id": p["id"], "heading": p["heading"], "module_id": p["module_id"], "module_title": modules[p["module_id"]]["title"]}

    return [
        {**o, "firm_passage": ref(o["firm_passage_id"]), "baseline_passage": ref(o["baseline_passage_id"])}
        for o in overrides
        if o["firm_passage_id"] in passages and o["baseline_passage_id"] in passages
    ]


# ---------------------------------------------------------------------------
# Baseline modules
# ---------------------------------------------------------------------------

def _baseline_modules(repo: Repo, firm_id: str) -> list[dict]:
    base_id = baseline_firm_id(repo)
    if base_id is None:
        return []
    modules = repo.select("modules", {"firm_id": base_id, "status": "approved"})
    settings = {s["module_id"]: s for s in repo.select("firm_baseline_modules", {"firm_id": firm_id})}
    passages = repo.select("module_passages", {"module_id": [m["id"] for m in modules]}, order="ordinal")
    critical = {r["passage_id"]: r["is_critical"] for r in repo.select("firm_baseline_passages", {"firm_id": firm_id})}
    overridden = {
        o["baseline_passage_id"]: o["id"]
        for o in repo.select("baseline_overrides", {"firm_id": firm_id, "status": "confirmed"})
    }

    out = []
    for m in modules:
        s = settings.get(m["id"], {})
        out.append({
            **m,
            "priority": s.get("priority") or m["priority"],
            "is_required": m["is_required"] if s.get("is_required") is None else s["is_required"],
            "ordinal": s["ordinal"] if s.get("ordinal") is not None else BASELINE_ORDINAL_OFFSET + m["ordinal"],
            "is_hidden": bool(s.get("is_hidden")),
            "passages": [
                {**p, "is_critical": critical.get(p["id"], False), "overridden_by": overridden.get(p["id"])}
                for p in passages
                if p["module_id"] == m["id"]
            ],
        })
    return sorted(out, key=module_sort_key)


@router.get("/baseline/modules", response_model=list[BaselineModuleOut])
def list_baseline_modules(profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """The shared AEC baseline modules, with this firm's settings, including hidden ones."""
    return _baseline_modules(repo, profile.firm_id)


@router.patch("/baseline/modules/{module_id}", response_model=BaselineModuleOut)
def update_baseline_module(
    module_id: str,
    body: BaselineModuleUpdate,
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Set this firm's priority, required flag, order, or visibility for a baseline module."""
    modules = {m["id"]: m for m in _baseline_modules(repo, profile.firm_id)}
    if not _valid_uuid(module_id) or module_id not in modules:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Baseline module not found")

    changes = {f: getattr(body, f) for f in ("priority", "is_required", "ordinal", "is_hidden") if getattr(body, f) is not None}
    if changes:
        existing = repo.select_one("firm_baseline_modules", {"firm_id": profile.firm_id, "module_id": module_id})
        if existing:
            repo.update("firm_baseline_modules", existing["id"], {**changes, "updated_at": _now()})
        else:
            repo.insert("firm_baseline_modules", [{"firm_id": profile.firm_id, "module_id": module_id, **changes}])
    return next(m for m in _baseline_modules(repo, profile.firm_id) if m["id"] == module_id)


# ---------------------------------------------------------------------------
# Overrides
# ---------------------------------------------------------------------------

@router.patch("/overrides/{override_id}", response_model=OverrideOut)
def update_override(
    override_id: str,
    body: OverrideUpdate,
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Confirm (employees then see the firm's version) or dismiss a proposed override."""
    override = repo.select_one("baseline_overrides", {"id": override_id, "firm_id": profile.firm_id}) if _valid_uuid(override_id) else None
    if override is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Override not found")
    if body.status == "confirmed" and override["status"] != "confirmed":
        others = repo.select("baseline_overrides", {
            "firm_id": profile.firm_id, "baseline_passage_id": override["baseline_passage_id"], "status": "confirmed",
        })
        if others:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Another firm passage already overrides this baseline passage. Dismiss that override first.",
            )
    if body.status != override["status"]:
        reviewed = body.status != "proposed"
        override = repo.update("baseline_overrides", override_id, {
            "status": body.status,
            "reviewed_by": profile.id if reviewed else None,
            "reviewed_at": _now() if reviewed else None,
        })
    return override_views(repo, [override])[0]
