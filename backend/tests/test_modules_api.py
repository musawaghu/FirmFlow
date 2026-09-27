import json

import pytest

from app.routers import modules as modules_router
from app.services import grounding
from tests.claude_mock import error_client, mock_client, sse
from tests.conftest import FIRM_A, FIRM_B, auth

SECTION_CONTENT = "Timesheets are due every Friday by 5:00 PM. Round to the nearest quarter hour."


@pytest.fixture
def seeded(repo):
    """One processed manual in firm A with two draft modules, and one module in firm B."""
    manual = repo.insert("manuals", [{"firm_id": FIRM_A, "title": "Handbook", "file_path": "x", "file_type": "pdf", "status": "processed"}])[0]
    section = repo.insert("source_sections", [{
        "manual_id": manual["id"], "ordinal": 21, "heading": "6. TIMESHEETS", "content": SECTION_CONTENT,
        "page_start": 9, "page_end": 9,
    }])[0]
    timesheets, bim, later = repo.insert("modules", [
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "Timesheets", "ordinal": 0, "priority": "day_1"},
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "How to Use BIM", "ordinal": 1, "priority": "day_1"},
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "Studio History", "ordinal": 2, "priority": "later", "is_required": False},
    ])
    ok, flagged, bim_ok, later_ok = repo.insert("module_passages", [
        {"module_id": timesheets["id"], "source_section_id": section["id"], "ordinal": 0, "heading": "Deadline",
         "content": "Submit your timesheet every Friday by 5:00 PM.", "kind": "text", "grounding_ok": True},
        {"module_id": timesheets["id"], "source_section_id": section["id"], "ordinal": 1, "heading": None,
         "content": "Round to the nearest quarter hour or you will be written up.", "kind": "text", "grounding_ok": False,
         "unsupported_spans": [{"text": "or you will be written up", "reason": "No consequence stated.", "check": "model", "located": True}]},
        {"module_id": bim["id"], "source_section_id": section["id"], "ordinal": 0, "heading": None,
         "content": "Round to the nearest quarter hour.", "kind": "text", "grounding_ok": True},
        {"module_id": later["id"], "source_section_id": section["id"], "ordinal": 0, "heading": None,
         "content": "Round to the nearest quarter hour.", "kind": "text", "grounding_ok": True},
    ])
    other_firm = repo.insert("modules", [{"firm_id": FIRM_B, "title": "Other", "ordinal": 0, "priority": "day_1", "status": "approved"}])[0]
    return {"timesheets": timesheets, "bim": bim, "later": later, "ok": ok, "flagged": flagged,
            "bim_ok": bim_ok, "other_firm": other_firm, "section": section}


@pytest.fixture
def grounding_reply(monkeypatch):
    """What the model check answers on passage edits; tests can change it."""
    state = {"payload": {"unsupported": []}, "requests": [], "client": None}

    def check(passages):
        client = state["client"] or mock_client(sse(state["payload"]), state["requests"])
        return grounding.check_passages(passages, client=client)

    monkeypatch.setattr(modules_router, "check_passages", check)
    return state


def patch_module(api, module_id, token="admin-a", **body):
    return api.patch(f"/api/modules/{module_id}", json=body, headers=auth(token))


def patch_passage(api, passage_id, token="admin-a", **body):
    return api.patch(f"/api/passages/{passage_id}", json=body, headers=auth(token))


def approve(api, repo, *modules):
    for m in modules:
        for p in repo.select("module_passages", {"module_id": m["id"]}):
            repo.update("module_passages", p["id"], {"grounding_ok": True})
        assert patch_module(api, m["id"], status="approved").status_code == 200


# ---------------------------------------------------------------------------
# PATCH /api/modules/{id}
# ---------------------------------------------------------------------------

def test_approve_clean_module(api, repo, seeded):
    res = patch_module(api, seeded["bim"]["id"], status="approved", priority="week_1")
    assert res.status_code == 200, res.text
    module = res.json()
    assert (module["status"], module["priority"]) == ("approved", "week_1")
    assert [p["id"] for p in module["passages"]] == [seeded["bim_ok"]["id"]]
    stored = repo.select_one("modules", {"id": seeded["bim"]["id"]})
    assert stored["reviewed_by"] == "user-admin-a" and stored["reviewed_at"] and stored["updated_at"]


def test_approval_blocked_by_flagged_passages(api, repo, seeded):
    res = patch_module(api, seeded["timesheets"]["id"], status="approved")
    assert res.status_code == 409
    assert res.json()["detail"]["passage_ids"] == [seeded["flagged"]["id"]]
    assert repo.select_one("modules", {"id": seeded["timesheets"]["id"]})["status"] == "draft"

    # An unchecked passage (grounding_ok null) blocks approval too.
    repo.update("module_passages", seeded["flagged"]["id"], {"grounding_ok": None})
    assert patch_module(api, seeded["timesheets"]["id"], status="approved").status_code == 409

    res = patch_module(api, seeded["timesheets"]["id"], status="approved", confirm_flagged=True)
    assert res.status_code == 200 and res.json()["status"] == "approved"


def test_module_without_passages_cannot_be_approved(api, repo, seeded):
    repo.delete("module_passages", {"module_id": seeded["bim"]["id"]})
    assert patch_module(api, seeded["bim"]["id"], status="approved").status_code == 409


def test_reject_and_return_to_draft(api, repo, seeded):
    res = patch_module(api, seeded["bim"]["id"], status="rejected")
    assert res.json()["status"] == "rejected"
    assert repo.select_one("modules", {"id": seeded["bim"]["id"]})["reviewed_by"] == "user-admin-a"

    res = patch_module(api, seeded["bim"]["id"], status="draft")
    assert res.json()["status"] == "draft"
    assert repo.select_one("modules", {"id": seeded["bim"]["id"]})["reviewed_at"] is None


def test_edit_title_and_summary(api, seeded):
    res = patch_module(api, seeded["bim"]["id"], title="  BIM Basics ", summary="Working with Revit.")
    assert (res.json()["title"], res.json()["summary"]) == ("BIM Basics", "Working with Revit.")
    assert patch_module(api, seeded["bim"]["id"], title="   ").status_code == 422


def test_approved_module_content_is_locked(api, repo, seeded):
    approve(api, repo, seeded["bim"])
    assert patch_module(api, seeded["bim"]["id"], title="New").status_code == 409
    # Non-content settings can still change.
    assert patch_module(api, seeded["bim"]["id"], priority="later", is_required=False, ordinal=5).status_code == 200
    # Returning to draft and editing in one request is allowed.
    res = patch_module(api, seeded["bim"]["id"], status="draft", title="New")
    assert (res.json()["status"], res.json()["title"]) == ("draft", "New")


def test_module_patch_is_admin_only_and_firm_scoped(api, seeded):
    assert patch_module(api, seeded["bim"]["id"], token="employee-a", status="approved").status_code == 403
    assert patch_module(api, seeded["bim"]["id"], token="admin-b", status="approved").status_code == 404
    assert patch_module(api, seeded["other_firm"]["id"], status="draft").status_code == 404
    assert patch_module(api, "nope", status="draft").status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/passages/{id}
# ---------------------------------------------------------------------------

def test_editing_a_passage_regrounds_it(api, repo, seeded, grounding_reply):
    res = patch_passage(api, seeded["flagged"]["id"], content="Round your hours to the nearest quarter hour.")
    assert res.status_code == 200, res.text
    passage = res.json()
    assert passage["grounding_ok"] is True and passage["unsupported_spans"] == []
    assert passage["grounding_error"] is None

    prompt = json.loads(grounding_reply["requests"][0].content)["messages"][0]["content"]
    assert SECTION_CONTENT in prompt and "Round your hours" in prompt

    # The module can now be approved without confirming anything.
    assert patch_module(api, seeded["timesheets"]["id"], status="approved").status_code == 200


def test_edit_that_adds_facts_is_flagged(api, seeded, grounding_reply):
    grounding_reply["payload"] = {"unsupported": [{"passage_id": "P1", "text": "Ask Tom", "reason": "Not in source."}]}
    passage = patch_passage(api, seeded["ok"]["id"], content="Submit every Friday by 6:00 PM. Ask Tom.").json()
    assert passage["grounding_ok"] is False
    assert [(s["text"], s["check"]) for s in passage["unsupported_spans"]] == [("6:00", "rule"), ("Ask Tom", "model")]


def test_heading_edit_is_checked_too(api, seeded, grounding_reply):
    passage = patch_passage(api, seeded["ok"]["id"], heading="Due by 4 PM").json()
    assert passage["heading"] == "Due by 4 PM"
    assert passage["grounding_ok"] is False


def test_failed_recheck_saves_edit_as_unchecked(api, seeded, grounding_reply):
    grounding_reply["client"] = error_client(529, "Overloaded")
    res = patch_passage(api, seeded["ok"]["id"], content="Submit every Friday by 5:00 PM.")
    assert res.status_code == 200
    passage = res.json()
    assert passage["content"] == "Submit every Friday by 5:00 PM."
    assert passage["grounding_ok"] is None and "529" in passage["grounding_error"]


def test_critical_flag_and_kind_skip_the_check(api, seeded, grounding_reply):
    passage = patch_passage(api, seeded["ok"]["id"], is_critical=True, kind="checklist").json()
    assert (passage["is_critical"], passage["kind"], passage["grounding_ok"]) == (True, "checklist", True)
    assert grounding_reply["requests"] == []


def test_unchanged_content_skips_the_check(api, seeded, grounding_reply):
    patch_passage(api, seeded["ok"]["id"], content=seeded["ok"]["content"], heading=" Deadline ")
    assert grounding_reply["requests"] == []


def test_approved_passages_are_locked_except_critical(api, repo, seeded, grounding_reply):
    approve(api, repo, seeded["bim"])
    assert patch_passage(api, seeded["bim_ok"]["id"], content="Changed.").status_code == 409
    res = patch_passage(api, seeded["bim_ok"]["id"], is_critical=True)
    assert res.status_code == 200 and res.json()["is_critical"] is True


def test_passage_patch_validation_and_scope(api, seeded):
    assert patch_passage(api, seeded["ok"]["id"], content="  ").status_code == 422
    assert patch_passage(api, seeded["ok"]["id"], token="admin-b", is_critical=True).status_code == 404
    assert patch_passage(api, seeded["ok"]["id"], token="employee-a", is_critical=True).status_code == 403
    assert patch_passage(api, "nope", is_critical=True).status_code == 404


# ---------------------------------------------------------------------------
# Employees: GET /api/modules and progress
# ---------------------------------------------------------------------------

def test_employees_see_only_approved_modules_in_priority_order(api, repo, seeded):
    repo.update("modules", seeded["bim"]["id"], {"priority": "week_1"})
    approve(api, repo, seeded["later"], seeded["bim"])

    res = api.get("/api/modules", headers=auth("employee-a")).json()
    assert res["full_name"] == "Alex Rivera"
    assert [m["title"] for m in res["modules"]] == ["How to Use BIM", "Studio History"]  # Timesheets is still a draft
    assert all(m["progress"] == "not_started" for m in res["modules"])
    assert set(res["modules"][0]["passages"][0]) == {  # no grounding details
        "id", "ordinal", "heading", "content", "kind", "overridden_by_firm", "firm_note", "firm_passage_id"}
    assert res["modules"][0]["layer"] == "firm"
    assert (res["required_modules"], res["completed_required"], res["final_check_unlocked"]) == (1, 0, False)

    assert api.get("/api/modules", headers=auth("admin-b")).json()["modules"][0]["title"] == "Other"


def test_progress_flow_unlocks_final_check(api, repo, seeded):
    approve(api, repo, seeded["timesheets"], seeded["bim"], seeded["later"])
    url = lambda m: f"/api/modules/{seeded[m]['id']}/progress"  # noqa: E731

    started = api.post(url("timesheets"), json={"status": "in_progress"}, headers=auth("employee-a")).json()
    assert started["status"] == "in_progress" and started["started_at"] and started["completed_at"] is None

    done = api.post(url("timesheets"), json={"status": "completed"}, headers=auth("employee-a")).json()
    assert done["status"] == "completed" and done["started_at"] == started["started_at"] and done["completed_at"]

    # Completing never goes backwards.
    again = api.post(url("timesheets"), json={"status": "in_progress"}, headers=auth("employee-a")).json()
    assert again["status"] == "completed"

    api.post(url("bim"), json={"status": "completed"}, headers=auth("employee-a"))
    res = api.get("/api/modules", headers=auth("employee-a")).json()
    assert (res["required_modules"], res["completed_required"], res["final_check_unlocked"]) == (2, 2, True)
    assert len(repo.select("module_progress", {"profile_id": "user-employee-a"})) == 2

    # Progress is per person.
    other = api.get("/api/modules", headers=auth("admin-a")).json()
    assert other["completed_required"] == 0


def test_progress_only_on_approved_modules_in_own_firm(api, seeded):
    body = {"status": "in_progress"}
    assert api.post(f"/api/modules/{seeded['bim']['id']}/progress", json=body, headers=auth("employee-a")).status_code == 404
    assert api.post(f"/api/modules/{seeded['other_firm']['id']}/progress", json=body, headers=auth("employee-a")).status_code == 404
    assert api.post(f"/api/modules/{seeded['other_firm']['id']}/progress", json={"status": "done"}, headers=auth("admin-b")).status_code == 422
