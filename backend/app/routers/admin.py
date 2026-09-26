"""Admin dashboard data."""

from datetime import datetime

from fastapi import APIRouter, Depends

from app.auth import Profile, require_admin
from app.db import Repo, get_repo
from app.routers.quiz import section_links
from app.schemas import AdminProgressOut, FailedQuestionOut, UnansweredOut
from app.services.progress import final_check_unlocked, required_progress

router = APIRouter(prefix="/api/admin", tags=["admin"])

PRIORITY_ORDER = {"day_1": 0, "week_1": 1, "later": 2}


@router.get("/progress", response_model=AdminProgressOut)
def progress(profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """Onboarding progress for every employee in the firm, alphabetical."""
    employees = repo.select("profiles", {"firm_id": profile.firm_id, "role": "employee"}, order="full_name")
    modules = repo.select("modules", {"firm_id": profile.firm_id, "status": "approved"})
    modules.sort(key=lambda m: (PRIORITY_ORDER.get(m["priority"], 9), m["ordinal"], m["title"]))
    ids = [e["id"] for e in employees]
    progress_rows = repo.select("module_progress", {"profile_id": ids})
    attempts = repo.select("quiz_attempts", {"profile_id": ids}, order="started_at")

    out = []
    for employee in employees:
        rows = [r for r in progress_rows if r["profile_id"] == employee["id"]]
        status_by_module = {r["module_id"]: r["status"] for r in rows}
        required, completed = required_progress(modules, status_by_module)
        mine = [a for a in attempts if a["profile_id"] == employee["id"]]
        final_check = _final_check(mine, final_check_unlocked(required, completed))

        if final_check["status"] == "completed":
            stage = "complete"
        elif required and completed == required:
            stage = "modules_done"
        elif rows or mine:
            stage = "in_progress"
        else:
            stage = "not_started"

        timestamps = [t for r in rows for t in (r.get("started_at"), r.get("completed_at")) if t]
        timestamps += [t for a in mine for t in (a.get("started_at"), a.get("completed_at")) if t]
        out.append({
            "profile_id": employee["id"],
            "full_name": employee["full_name"],
            "email": employee["email"],
            "start_date": employee.get("start_date"),
            "stage": stage,
            "required_modules": required,
            "completed_required": completed,
            "modules": [
                {"module_id": m["id"], "title": m["title"], "priority": m["priority"], "is_required": m["is_required"],
                 "status": status_by_module.get(m["id"], "not_started")}
                for m in modules
            ],
            "final_check": final_check,
            "last_activity_at": max(timestamps, key=datetime.fromisoformat) if timestamps else None,
        })
    return {"required_modules": sum(1 for m in modules if m["is_required"]), "employees": out}


def _final_check(attempts: list[dict], unlocked: bool) -> dict:
    completed = [a for a in attempts if a["status"] == "completed"]
    if completed:
        latest = completed[-1]
        status = "completed"
    else:
        latest = None
        status = "in_progress" if attempts else "not_started" if unlocked else "locked"
    return {
        "status": status,
        "score": latest["score"] if latest else None,
        "attempts": len(attempts),
        "completed_at": latest["completed_at"] if latest else None,
    }


@router.get("/failed-questions", response_model=list[FailedQuestionOut])
def failed_questions(profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """Final-check questions ranked by how often employees miss them on the first try."""
    questions = repo.select("quiz_questions", {"firm_id": profile.firm_id})
    first_tries = repo.select("quiz_answers", {"question_id": [q["id"] for q in questions], "try_number": 1})
    links = section_links(repo, [q["passage_id"] for q in questions])

    out = []
    for q in questions:
        tries = [a for a in first_tries if a["question_id"] == q["id"]]
        if not tries:
            continue
        misses = sum(1 for a in tries if not a["is_correct"])
        out.append({
            "question_id": q["id"],
            "prompt": q["prompt"],
            "type": q["type"],
            "status": q["status"],
            "first_tries": len(tries),
            "first_try_misses": misses,
            "miss_rate": round(misses / len(tries), 3),
            "link": links.get(q["passage_id"]),
        })
    return sorted(out, key=lambda r: (-r["first_try_misses"], -r["miss_rate"], r["prompt"]))


@router.get("/unanswered", response_model=list[UnansweredOut])
def unanswered(profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """Assistant questions that fell back to the default contact, newest first."""
    logs = repo.select("chat_logs", {"firm_id": profile.firm_id, "used_fallback": True}, order="created_at")
    return list(reversed(logs))
