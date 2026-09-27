"""scripts/reset_demo.py deletes an employee's onboarding records. It must touch only that employee."""

import re
from pathlib import Path

import pytest

from scripts import reset_demo
from tests.conftest import FIRM_A

SCHEMA = Path(__file__).resolve().parents[2] / "supabase" / "schema.sql"


@pytest.fixture
def records(repo, monkeypatch):
    """Alex and Jamie (employees) and Priya (admin) at firm A, each with progress, an attempt, and chat history."""
    repo.insert("profiles", [{"id": "user-employee-a2", "firm_id": FIRM_A, "role": "employee",
                              "full_name": "Jamie Cho", "email": "jamie@a.example"}])
    module = repo.insert("modules", [{"firm_id": FIRM_A, "title": "Timesheets", "status": "approved"}])[0]
    question = repo.insert("quiz_questions", [{"firm_id": FIRM_A, "passage_id": "p1", "type": "multiple_choice",
                                               "prompt": "When are timesheets due?", "status": "approved"}])[0]
    for profile_id in ("user-employee-a", "user-employee-a2", "user-admin-a"):
        repo.insert("module_progress", [{"profile_id": profile_id, "module_id": module["id"], "status": "completed"}])
        repo.insert("quiz_attempts", [{"firm_id": FIRM_A, "profile_id": profile_id, "question_ids": [question["id"]],
                                       "status": "completed", "score": 100.0}])
        repo.insert("chat_logs", [{"firm_id": FIRM_A, "profile_id": profile_id, "question": "Who handles payroll?",
                                   "used_fallback": False}])
    monkeypatch.setattr(reset_demo, "get_repo", lambda: repo)
    return {"module": module, "question": question}


def run(monkeypatch, *args):
    monkeypatch.setattr("sys.argv", ["reset_demo", *args])
    reset_demo.main()


def owners(repo, table):
    return sorted(r["profile_id"] for r in repo.select(table))


def test_resets_only_the_named_employee(repo, records, monkeypatch, capsys):
    run(monkeypatch, "alex@a.example")

    for table in ("module_progress", "quiz_attempts", "chat_logs"):
        assert owners(repo, table) == ["user-admin-a", "user-employee-a2"], table
    # Content and people are kept.
    assert [m["id"] for m in repo.select("modules")] == [records["module"]["id"]]
    assert [q["id"] for q in repo.select("quiz_questions")] == [records["question"]["id"]]
    assert len(repo.select("profiles")) == 4
    assert capsys.readouterr().out.splitlines() == [
        "module_progress: deleted 1",
        "quiz_attempts: deleted 1",
        "chat_logs: deleted 1",
        "Reset Alex Rivera's onboarding.",
    ]


def test_running_again_deletes_nothing_more(repo, records, monkeypatch, capsys):
    run(monkeypatch, "alex@a.example")
    capsys.readouterr()
    run(monkeypatch, "alex@a.example")
    assert capsys.readouterr().out.splitlines()[:3] == [
        "module_progress: deleted 0", "quiz_attempts: deleted 0", "chat_logs: deleted 0"]
    assert owners(repo, "chat_logs") == ["user-admin-a", "user-employee-a2"]


@pytest.mark.parametrize(("email", "message"), [
    ("priya@a.example", "priya@a.example is an admin, not an employee; refusing to reset"),
    ("nobody@a.example", "No profile for nobody@a.example"),
])
def test_refuses_admins_and_unknown_people_without_deleting(repo, records, monkeypatch, capsys, email, message):
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, email)
    assert exit_info.value.code == 1
    assert capsys.readouterr().err.strip() == message
    for table in ("module_progress", "quiz_attempts", "chat_logs"):
        assert owners(repo, table) == ["user-admin-a", "user-employee-a", "user-employee-a2"], table


def test_database_removes_answers_with_their_attempt():
    """The script deletes quiz_attempts and relies on the schema to delete their quiz_answers."""
    table = re.search(r"create table quiz_answers \((.*?)\n\);", SCHEMA.read_text(), re.S).group(1)
    assert re.search(r"attempt_id\s+uuid not null references quiz_attempts \(id\) on delete cascade", table)
