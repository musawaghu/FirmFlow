"""Onboarding progress rules shared by the modules list and the final check."""

from app.db import Repo, Row


def required_progress(modules: list[Row], progress: dict[str, str]) -> tuple[int, int]:
    """(required approved modules, how many of them are completed) for one employee."""
    required = [m for m in modules if m["status"] == "approved" and m["is_required"]]
    completed = sum(1 for m in required if progress.get(m["id"]) == "completed")
    return len(required), completed


def final_check_unlocked(required: int, completed: int) -> bool:
    return required > 0 and completed == required


def load_progress(repo: Repo, firm_id: str, profile_id: str) -> tuple[list[Row], dict[str, str]]:
    modules = repo.select("modules", {"firm_id": firm_id, "status": "approved"})
    progress = {p["module_id"]: p["status"] for p in repo.select("module_progress", {"profile_id": profile_id})}
    return modules, progress
