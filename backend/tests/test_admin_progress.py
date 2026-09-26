import pytest

from tests.conftest import FIRM_A, FIRM_B, auth


@pytest.fixture
def seeded(repo):
    """Two required modules, one optional, one draft, and employees at every stage."""
    repo.insert("profiles", [
        {"id": "user-jamie", "firm_id": FIRM_A, "role": "employee", "full_name": "Jamie Cho", "email": "jamie@a.example", "start_date": "2026-09-28"},
        {"id": "user-sam", "firm_id": FIRM_A, "role": "employee", "full_name": "Sam Park", "email": "sam@a.example", "start_date": "2026-09-14"},
        {"id": "user-casey", "firm_id": FIRM_A, "role": "employee", "full_name": "Casey Diaz", "email": "casey@a.example", "start_date": "2026-09-01"},
        {"id": "user-other", "firm_id": FIRM_B, "role": "employee", "full_name": "Other Firm", "email": "o@b.example"},
    ])
    later, bim, time, draft = repo.insert("modules", [
        {"firm_id": FIRM_A, "title": "Studio History", "ordinal": 0, "priority": "later", "status": "approved", "is_required": False},
        {"firm_id": FIRM_A, "title": "How to Use BIM", "ordinal": 2, "priority": "day_1", "status": "approved"},
        {"firm_id": FIRM_A, "title": "Timesheets", "ordinal": 1, "priority": "day_1", "status": "approved"},
        {"firm_id": FIRM_A, "title": "Draft", "ordinal": 3, "priority": "day_1"},
    ])

    def progress(profile, module, status, started, completed=None):
        return {"profile_id": profile, "module_id": module["id"], "status": status, "started_at": started, "completed_at": completed}

    repo.insert("module_progress", [
        # Alex (employee-a): one module in progress.
        progress("user-employee-a", time, "in_progress", "2026-09-29T09:00:00+00:00"),
        # Sam: both required modules done, final check not started.
        progress("user-sam", time, "completed", "2026-09-15T09:00:00+00:00", "2026-09-15T10:00:00+00:00"),
        progress("user-sam", bim, "completed", "2026-09-16T09:00:00+00:00", "2026-09-16T11:00:00+00:00"),
        # Casey: everything done, including the final check.
        progress("user-casey", time, "completed", "2026-09-02T09:00:00+00:00", "2026-09-02T10:00:00+00:00"),
        progress("user-casey", bim, "completed", "2026-09-03T09:00:00+00:00", "2026-09-03T10:00:00+00:00"),
        # Draft modules never count.
        progress("user-casey", draft, "completed", "2026-09-03T09:00:00+00:00", "2026-09-03T09:30:00+00:00"),
    ])
    repo.insert("quiz_attempts", [
        {"firm_id": FIRM_A, "profile_id": "user-casey", "question_ids": [], "status": "completed", "score": 83.33,
         "started_at": "2026-09-04T09:00:00+00:00", "completed_at": "2026-09-04T09:05:00+00:00"},
    ])
    return {"later": later, "bim": bim, "time": time}


def get(api, token="admin-a"):
    return api.get("/api/admin/progress", headers=auth(token))


def test_progress_for_every_employee(api, seeded):
    res = get(api)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["required_modules"] == 2
    rows = {e["full_name"]: e for e in body["employees"]}
    assert list(rows) == ["Alex Rivera", "Casey Diaz", "Jamie Cho", "Sam Park"]  # alphabetical, employees only, own firm

    assert [(n, rows[n]["stage"], rows[n]["completed_required"], rows[n]["final_check"]["status"]) for n in rows] == [
        ("Alex Rivera", "in_progress", 0, "locked"),
        ("Casey Diaz", "complete", 2, "completed"),
        ("Jamie Cho", "not_started", 0, "locked"),
        ("Sam Park", "modules_done", 2, "not_started"),
    ]


def test_module_detail_follows_employee_order(api, seeded):
    alex = next(e for e in get(api).json()["employees"] if e["full_name"] == "Alex Rivera")
    assert [(m["title"], m["status"], m["is_required"]) for m in alex["modules"]] == [
        ("Timesheets", "in_progress", True),
        ("How to Use BIM", "not_started", True),
        ("Studio History", "not_started", False),
    ]


def test_final_check_and_activity_details(api, repo, seeded):
    rows = {e["full_name"]: e for e in get(api).json()["employees"]}
    casey = rows["Casey Diaz"]
    assert casey["final_check"] == {"status": "completed", "score": 83.33, "attempts": 1, "completed_at": "2026-09-04T09:05:00+00:00"}
    assert casey["last_activity_at"] == "2026-09-04T09:05:00+00:00"
    assert rows["Sam Park"]["last_activity_at"] == "2026-09-16T11:00:00+00:00"
    assert rows["Jamie Cho"]["last_activity_at"] is None
    assert rows["Jamie Cho"]["start_date"] == "2026-09-28"

    # A started attempt shows as in progress.
    repo.insert("quiz_attempts", [{"firm_id": FIRM_A, "profile_id": "user-sam", "question_ids": [], "status": "in_progress",
                                   "started_at": "2026-09-17T09:00:00+00:00"}])
    sam = next(e for e in get(api).json()["employees"] if e["full_name"] == "Sam Park")
    assert (sam["stage"], sam["final_check"]["status"], sam["final_check"]["attempts"]) == ("modules_done", "in_progress", 1)


def test_newly_approved_module_reopens_progress(api, repo, seeded):
    repo.insert("modules", [{"firm_id": FIRM_A, "title": "PTO", "ordinal": 4, "priority": "week_1", "status": "approved"}])
    sam = next(e for e in get(api).json()["employees"] if e["full_name"] == "Sam Park")
    assert (sam["stage"], sam["completed_required"], sam["required_modules"]) == ("in_progress", 2, 3)
    assert sam["final_check"]["status"] == "locked"


def test_progress_is_admin_only_and_firm_scoped(api, seeded):
    assert get(api, "employee-a").status_code == 403
    assert [e["full_name"] for e in get(api, "admin-b").json()["employees"]] == ["Other Firm"]
