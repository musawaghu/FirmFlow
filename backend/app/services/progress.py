"""Onboarding progress rules shared by the modules list and the final check."""

from app.db import Repo, Row
from app.services.content import firm_content


def required_progress(modules: list[Row], progress: dict[str, str]) -> tuple[int, int]:
    """(required approved modules, how many of them are completed) for one employee."""
    required = [m for m in modules if m["status"] == "approved" and m["is_required"]]
    completed = sum(1 for m in required if progress.get(m["id"]) == "completed")
    return len(required), completed


def final_check_unlocked(required: int, completed: int) -> bool:
    return required > 0 and completed == required


def profile_progress(repo: Repo, profile_id: str) -> dict[str, str]:
    """module id -> this employee's status."""
    return {p["module_id"]: p["status"] for p in repo.select("module_progress", {"profile_id": profile_id})}


def load_progress(repo: Repo, firm_id: str, profile_id: str) -> tuple[list[Row], dict[str, str]]:
    """The modules the firm's employees see (firm and baseline), and this employee's progress."""
    return firm_content(repo, firm_id).modules, profile_progress(repo, profile_id)
