"""AEC baseline + firm overlay: what employees see, firm settings, overrides, and critical passages."""

import pytest

from app.routers import chat as chat_router
from app.services.assistant import AssistantResult
from app.services.content import firm_content
from tests.conftest import FIRM_A, FIRM_B, auth

BASELINE = "b0000000-0000-4000-8000-000000000001"


@pytest.fixture
def layered(repo):
    """An approved baseline with two modules, and firm A with one approved module that renumbers sheets."""
    repo.insert("firms", [
        {"id": BASELINE, "name": "FIRM FLOW AEC Baseline", "slug": "firmflow-baseline", "is_baseline": True},
        {"id": FIRM_A, "name": "Studio Meridian Architects", "slug": "studio-meridian"},
        {"id": FIRM_B, "name": "Other Firm", "slug": "other"},
    ])
    base_manual = repo.insert("manuals", [{"firm_id": BASELINE, "title": "AEC Baseline Guide", "file_path": "b", "file_type": "pdf", "status": "processed"}])[0]
    base_section = repo.insert("source_sections", [{"manual_id": base_manual["id"], "ordinal": 1, "heading": "Drawing sets",
                                                    "content": "Number sheets like A1.01.", "page_start": 1, "page_end": 1}])[0]
    sets, consultants = repo.insert("modules", [
        {"firm_id": BASELINE, "manual_id": base_manual["id"], "title": "Drawing Set Organization", "ordinal": 0,
         "priority": "day_1", "status": "approved"},
        {"firm_id": BASELINE, "manual_id": base_manual["id"], "title": "Consultant Coordination", "ordinal": 1,
         "priority": "week_1", "status": "approved"},
    ])
    sheet, order, coord = repo.insert("module_passages", [
        {"module_id": sets["id"], "source_section_id": base_section["id"], "ordinal": 0, "heading": "Sheet numbers",
         "content": "Number sheets like A1.01: discipline, sheet type, sequence.", "kind": "text", "grounding_ok": True},
        {"module_id": sets["id"], "source_section_id": base_section["id"], "ordinal": 1, "heading": "Set order",
         "content": "General sheets come first.", "kind": "text", "grounding_ok": True},
        {"module_id": consultants["id"], "source_section_id": base_section["id"], "ordinal": 0, "heading": "Meetings",
         "content": "Attend coordination meetings.", "kind": "text", "grounding_ok": True},
    ])

    manual = repo.insert("manuals", [{"firm_id": FIRM_A, "title": "Handbook", "file_path": "a", "file_type": "pdf", "status": "processed"}])[0]
    section = repo.insert("source_sections", [{"manual_id": manual["id"], "ordinal": 1, "heading": "21. DRAWING STANDARDS",
                                               "content": "We number sheets A-101, never A1.01.", "page_start": 23, "page_end": 23}])[0]
    tech, draft = repo.insert("modules", [
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "Technology", "ordinal": 0, "priority": "day_1", "status": "approved"},
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "Draft", "ordinal": 1, "priority": "day_1"},
    ])
    firm_sheet = repo.insert("module_passages", [
        {"module_id": tech["id"], "source_section_id": section["id"], "ordinal": 0, "heading": "Sheet numbering",
         "content": "Studio Meridian numbers sheets A-101, never A1.01.", "kind": "text", "grounding_ok": True},
    ])[0]
    override = repo.insert("baseline_overrides", [{
        "firm_id": FIRM_A, "manual_id": manual["id"], "firm_passage_id": firm_sheet["id"], "baseline_passage_id": sheet["id"],
        "firm_excerpt": "A-101, never A1.01", "baseline_excerpt": "A1.01", "difference": "Baseline A1.01; firm A-101.",
    }])[0]
    return {"sets": sets, "consultants": consultants, "sheet": sheet, "order": order, "coord": coord,
            "tech": tech, "firm_sheet": firm_sheet, "override": override, "manual": manual}


def modules(api, token="employee-a"):
    return api.get("/api/modules", headers=auth(token)).json()


def confirm(api, override_id, token="admin-a"):
    return api.patch(f"/api/overrides/{override_id}", json={"status": "confirmed"}, headers=auth(token))


def passage(module, heading):
    return next(p for p in module["passages"] if p["heading"] == heading or p["id"] == heading)


# ---------------------------------------------------------------------------
# What employees see
# ---------------------------------------------------------------------------

def test_employees_see_firm_modules_then_baseline(api, layered):
    res = modules(api)
    assert [(m["title"], m["layer"], m["priority"]) for m in res["modules"]] == [
        ("Technology", "firm", "day_1"),
        ("Drawing Set Organization", "baseline", "day_1"),
        ("Consultant Coordination", "baseline", "week_1"),
    ]
    assert res["required_modules"] == 3


def test_baseline_is_shared_but_settings_are_per_firm(api, repo, layered):
    res = api.patch(f"/api/baseline/modules/{layered['consultants']['id']}",
                    json={"is_hidden": True}, headers=auth())
    assert res.status_code == 200, res.text
    assert res.json()["is_hidden"] is True
    api.patch(f"/api/baseline/modules/{layered['sets']['id']}",
              json={"priority": "week_1", "is_required": False, "ordinal": 5}, headers=auth())

    mine = modules(api)
    assert [(m["title"], m["priority"], m["is_required"]) for m in mine["modules"]] == [
        ("Technology", "day_1", True), ("Drawing Set Organization", "week_1", False),
    ]
    assert mine["required_modules"] == 1
    # The admin still sees hidden baseline modules, with this firm's settings.
    listed = api.get("/api/baseline/modules", headers=auth()).json()
    assert [(m["title"], m["is_hidden"], m["ordinal"]) for m in listed] == [
        ("Drawing Set Organization", False, 5), ("Consultant Coordination", True, 1001),
    ]
    # Firm B is unaffected.
    other = api.get("/api/baseline/modules", headers=auth("admin-b")).json()
    assert [(m["title"], m["is_hidden"], m["priority"]) for m in other] == [
        ("Drawing Set Organization", False, "day_1"), ("Consultant Coordination", False, "week_1"),
    ]
    assert len(repo.select("firm_baseline_modules")) == 2  # one row per firm and module, updated in place


def test_baseline_module_settings_need_an_admin_and_a_baseline_module(api, layered):
    assert api.patch(f"/api/baseline/modules/{layered['sets']['id']}", json={"is_hidden": True}, headers=auth("employee-a")).status_code == 403
    assert api.patch(f"/api/baseline/modules/{layered['tech']['id']}", json={"is_hidden": True}, headers=auth()).status_code == 404
    assert api.patch("/api/baseline/modules/not-a-uuid", json={}, headers=auth()).status_code == 404


def test_baseline_modules_cannot_be_approved_or_edited_by_a_firm(api, layered):
    assert api.patch(f"/api/modules/{layered['sets']['id']}", json={"status": "rejected"}, headers=auth()).status_code == 404


# ---------------------------------------------------------------------------
# Overrides: the firm's version wins once confirmed
# ---------------------------------------------------------------------------

def test_proposed_override_changes_nothing(api, layered):
    sets = modules(api)["modules"][1]
    assert passage(sets, "Sheet numbers")["content"].startswith("Number sheets like A1.01")
    assert passage(sets, "Sheet numbers")["overridden_by_firm"] is False


def test_confirmed_override_shows_the_firm_version_with_a_note(api, layered):
    res = confirm(api, layered["override"]["id"])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "confirmed"
    assert (body["firm_passage"]["module_title"], body["baseline_passage"]["module_title"]) == ("Technology", "Drawing Set Organization")

    sets = modules(api)["modules"][1]
    overridden = passage(sets, layered["sheet"]["id"])
    assert overridden["content"] == "Studio Meridian numbers sheets A-101, never A1.01."
    assert overridden["heading"] == "Sheet numbering"
    assert overridden["overridden_by_firm"] is True
    assert overridden["firm_note"] == "Studio Meridian Architects does this differently."
    assert overridden["firm_passage_id"] == layered["firm_sheet"]["id"]
    assert passage(sets, "Set order")["overridden_by_firm"] is False

    # Other firms still see the baseline.
    other = modules(api, "admin-b")["modules"]
    other_sets = next(m for m in other if m["title"] == "Drawing Set Organization")
    assert passage(other_sets, "Sheet numbers")["content"].startswith("Number sheets like A1.01")


def test_dismissing_restores_the_baseline(api, layered):
    confirm(api, layered["override"]["id"])
    res = api.patch(f"/api/overrides/{layered['override']['id']}", json={"status": "dismissed"}, headers=auth())
    assert res.json()["status"] == "dismissed"
    assert passage(modules(api)["modules"][1], "Sheet numbers")["overridden_by_firm"] is False


def test_override_only_applies_while_the_firm_module_is_approved(api, repo, layered):
    confirm(api, layered["override"]["id"])
    repo.update("modules", layered["tech"]["id"], {"status": "draft"})
    sets = modules(api)["modules"][0]
    assert passage(sets, "Sheet numbers")["overridden_by_firm"] is False


def test_one_confirmed_override_per_baseline_passage(api, repo, layered):
    confirm(api, layered["override"]["id"])
    second = repo.insert("module_passages", [{
        "module_id": layered["tech"]["id"], "source_section_id": layered["firm_sheet"]["source_section_id"], "ordinal": 1,
        "heading": "More", "content": "Sheets are A-101.", "kind": "text", "grounding_ok": True,
    }])[0]
    other = repo.insert("baseline_overrides", [{
        "firm_id": FIRM_A, "manual_id": layered["manual"]["id"], "firm_passage_id": second["id"],
        "baseline_passage_id": layered["sheet"]["id"], "firm_excerpt": "A-101", "baseline_excerpt": "A1.01", "difference": "d",
    }])[0]
    assert confirm(api, other["id"]).status_code == 409


def test_overrides_are_firm_scoped(api, layered):
    assert confirm(api, layered["override"]["id"], token="admin-b").status_code == 404
    assert confirm(api, layered["override"]["id"], token="employee-a").status_code == 403


# ---------------------------------------------------------------------------
# Critical baseline passages, final check, assistant, admin progress
# ---------------------------------------------------------------------------

def test_firm_marks_baseline_passages_critical_for_itself(api, repo, layered):
    res = api.patch(f"/api/passages/{layered['coord']['id']}", json={"is_critical": True}, headers=auth())
    assert res.status_code == 200, res.text
    assert res.json()["is_critical"] is True
    api.patch(f"/api/passages/{layered['coord']['id']}", json={"is_critical": True}, headers=auth())
    assert len(repo.select("firm_baseline_passages")) == 1

    assert [p["id"] for p in firm_content(repo, FIRM_A).critical_passages()] == [layered["coord"]["id"]]
    assert firm_content(repo, FIRM_B).critical_passages() == []
    assert repo.select_one("module_passages", {"id": layered["coord"]["id"]})["is_critical"] is False  # shared row untouched


def test_baseline_passage_text_cannot_be_edited(api, layered):
    res = api.patch(f"/api/passages/{layered['coord']['id']}", json={"content": "Skip meetings."}, headers=auth())
    assert res.status_code == 409
    assert "shared by every firm" in res.json()["detail"]


def test_overridden_baseline_passage_is_not_quiz_material(api, repo, layered):
    api.patch(f"/api/passages/{layered['sheet']['id']}", json={"is_critical": True}, headers=auth())
    assert [p["id"] for p in firm_content(repo, FIRM_A).critical_passages()] == [layered["sheet"]["id"]]
    confirm(api, layered["override"]["id"])
    assert firm_content(repo, FIRM_A).critical_passages() == []


def test_final_check_waits_for_required_baseline_modules(api, layered):
    api.post(f"/api/modules/{layered['tech']['id']}/progress", json={"status": "completed"}, headers=auth("employee-a"))
    assert modules(api)["final_check_unlocked"] is False
    for m in ("sets", "consultants"):
        res = api.post(f"/api/modules/{layered[m]['id']}/progress", json={"status": "completed"}, headers=auth("employee-a"))
        assert res.status_code == 200, res.text
    assert modules(api)["final_check_unlocked"] is True


def test_progress_on_hidden_baseline_module_is_refused(api, layered):
    api.patch(f"/api/baseline/modules/{layered['consultants']['id']}", json={"is_hidden": True}, headers=auth())
    res = api.post(f"/api/modules/{layered['consultants']['id']}/progress", json={"status": "completed"}, headers=auth("employee-a"))
    assert res.status_code == 404


def test_assistant_sees_the_firm_rule_not_the_overridden_baseline(api, layered, monkeypatch):
    confirm(api, layered["override"]["id"])
    seen = {}

    def fake_ask(question, *, directory, index, employee_name):
        seen["ids"] = [p["id"] for p, _ in index.passages.values()]
        return AssistantResult(intent="where_is", answer="See the Technology module.", links=[], contacts=[], used_fallback=False)

    monkeypatch.setattr(chat_router, "ask", fake_ask)
    assert api.post("/api/chat", json={"question": "How do I number sheets?"}, headers=auth("employee-a")).status_code == 200
    assert layered["firm_sheet"]["id"] in seen["ids"]
    assert layered["sheet"]["id"] not in seen["ids"]
    assert layered["order"]["id"] in seen["ids"]  # the rest of the baseline is still there


def test_admin_progress_counts_baseline_modules(api, layered):
    res = api.get("/api/admin/progress", headers=auth()).json()
    assert res["required_modules"] == 3
    assert [(m["title"], m["layer"]) for m in res["employees"][0]["modules"]] == [
        ("Technology", "firm"), ("Drawing Set Organization", "baseline"), ("Consultant Coordination", "baseline"),
    ]
