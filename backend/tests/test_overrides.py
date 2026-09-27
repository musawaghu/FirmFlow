"""Detecting firm overrides of the AEC baseline."""

import json

import pytest

from app.routers import manuals as manuals_router
from app.services import enhancer, grounding, overrides, processing
from app.services.overrides import PassageText, detect_overrides, refresh_overrides
from tests.claude_mock import error_client, mock_client, sse
from tests.conftest import auth
from tests.test_baseline import layered  # noqa: F401  (fixture)
from tests.test_manuals_api import ENHANCEMENT, GROUNDING, upload

FIRM = [
    PassageText("f-sheet", "Technology", "Sheet numbering", "Studio Meridian numbers sheets A-101, never A1.01."),
    PassageText("f-time", "Operations", "Timesheets", "Submit your timesheet every Friday."),
]
BASE = [
    PassageText("b-sheet", "Drawing Set Organization", "Sheet numbers", "Number sheets like A1.01: discipline, sheet type, sequence."),
    PassageText("b-coord", "Consultant Coordination", "Meetings", "Attend coordination meetings."),
]


def reply(*items):
    return sse({"overrides": list(items)}, input_tokens=700, output_tokens=90)


def item(firm="F1", base="B1", firm_excerpt="A-101, never A1.01", base_excerpt="A1.01", difference="Baseline A1.01; firm A-101."):
    return {"firm_passage_id": firm, "baseline_passage_id": base, "firm_excerpt": firm_excerpt,
            "baseline_excerpt": base_excerpt, "difference": difference}


# ---------------------------------------------------------------------------
# detect_overrides()
# ---------------------------------------------------------------------------

def test_detect_keeps_overrides_whose_quotes_check_out():
    requests = []
    result = detect_overrides(FIRM, BASE, client=mock_client(reply(
        item(),
        item(firm_excerpt="  a-101,   NEVER a1.01 "),  # same pair again, sloppy quote: deduped
        item(firm="F2", base="B2", firm_excerpt="every Monday", base_excerpt="Attend"),  # quote not in the firm passage
        item(firm="F9"),  # unknown passage
    ), requests))

    assert [(o.firm_passage_key, o.baseline_passage_key, o.firm_excerpt, o.baseline_excerpt) for o in result.overrides] == [
        ("f-sheet", "b-sheet", "A-101, never A1.01", "A1.01"),
    ]
    assert len(result.warnings) == 2
    assert (result.input_tokens, result.output_tokens) == (700, 90)

    prompt = json.loads(requests[0].content)["messages"][0]["content"]
    assert '<passage id="B1" module="Drawing Set Organization">' in prompt
    assert '<passage id="F2" module="Operations">' in prompt
    assert prompt.index("<baseline_passages>") < prompt.index("<firm_passages>")


def test_detect_tolerates_whitespace_and_case_in_quotes():
    result = detect_overrides(FIRM, BASE, client=mock_client(reply(item(firm_excerpt="numbers  sheets a-101"))))
    assert result.overrides[0].firm_excerpt == "numbers sheets A-101"


def test_detect_skips_the_call_without_both_layers():
    assert detect_overrides([], BASE, client=error_client(500)).overrides == []
    assert detect_overrides(FIRM, [], client=error_client(500)).overrides == []


def test_detect_model_failure():
    with pytest.raises(overrides.OverrideError):
        detect_overrides(FIRM, BASE, client=error_client(529, "Overloaded"))


# ---------------------------------------------------------------------------
# refresh_overrides()
# ---------------------------------------------------------------------------

def test_refresh_replaces_proposals_and_keeps_decisions(repo, layered):
    first = {"firm_passage_id": "F1", "baseline_passage_id": "B1", "firm_excerpt": "A-101, never A1.01",
             "baseline_excerpt": "A1.01", "difference": "Baseline A1.01; firm A-101."}
    # The fixture's proposal is replaced by the fresh one.
    refresh_overrides(repo, layered["manual"], client=mock_client(reply(first)))
    rows = repo.select("baseline_overrides")
    assert [(r["status"], r["firm_passage_id"], r["baseline_passage_id"]) for r in rows] == [
        ("proposed", layered["firm_sheet"]["id"], layered["sheet"]["id"]),
    ]

    repo.update("baseline_overrides", rows[0]["id"], {"status": "dismissed"})
    refresh_overrides(repo, layered["manual"], client=mock_client(reply(first)))
    assert [r["status"] for r in repo.select("baseline_overrides")] == ["dismissed"]  # not proposed again


def test_refresh_does_nothing_for_the_baseline_itself_or_without_one(repo, layered):
    base_manual = repo.select_one("manuals", {"title": "AEC Baseline Guide"})
    assert refresh_overrides(repo, base_manual, client=error_client(500)).overrides == []
    repo.update("firms", "b0000000-0000-4000-8000-000000000001", {"is_baseline": False})
    assert refresh_overrides(repo, layered["manual"], client=error_client(500)).overrides == []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def detect_reply(monkeypatch):
    state = {"body": reply(item())}
    real = refresh_overrides
    monkeypatch.setattr(manuals_router, "refresh_overrides", lambda repo, manual: real(repo, manual, client=mock_client(state["body"])))
    return state


def test_detect_endpoint_lists_and_review_includes_overrides(api, repo, layered, detect_reply):
    mid = layered["manual"]["id"]
    res = api.post(f"/api/manuals/{mid}/overrides/detect", headers=auth())
    assert res.status_code == 200, res.text
    [o] = res.json()
    assert (o["status"], o["firm_passage"]["heading"], o["baseline_passage"]["module_title"]) == (
        "proposed", "Sheet numbering", "Drawing Set Organization")

    assert [x["id"] for x in api.get(f"/api/manuals/{mid}/overrides?status=proposed", headers=auth()).json()] == [o["id"]]
    assert api.get(f"/api/manuals/{mid}/overrides?status=confirmed", headers=auth()).json() == []
    assert [x["id"] for x in api.get(f"/api/manuals/{mid}/review", headers=auth()).json()["overrides"]] == [o["id"]]


def test_detect_endpoint_errors(api, repo, layered, detect_reply):
    mid = layered["manual"]["id"]
    detect_reply["body"] = "not used"
    repo.update("manuals", mid, {"status": "uploaded"})
    assert api.post(f"/api/manuals/{mid}/overrides/detect", headers=auth()).status_code == 409
    assert api.post(f"/api/manuals/{mid}/overrides/detect", headers=auth("admin-b")).status_code == 404


def test_detect_endpoint_model_failure(api, repo, layered, monkeypatch):
    monkeypatch.setattr(manuals_router, "refresh_overrides",
                        lambda repo, manual: refresh_overrides(repo, manual, client=error_client(529, "Overloaded")))
    res = api.post(f"/api/manuals/{layered['manual']['id']}/overrides/detect", headers=auth())
    assert res.status_code == 503 and "529" in res.json()["detail"]


# ---------------------------------------------------------------------------
# Processing runs detection
# ---------------------------------------------------------------------------

def processing_client(api, monkeypatch, override_body):
    claude = mock_client([sse(ENHANCEMENT), sse(GROUNDING, input_tokens=300, output_tokens=40)])
    monkeypatch.setattr(processing, "enhance_manual", lambda s, module_topics=None: enhancer.enhance_manual(s, module_topics=module_topics, client=claude))
    monkeypatch.setattr(processing, "check_enhancement", lambda e, s: grounding.check_enhancement(e, s, client=claude))
    real = refresh_overrides
    client = override_body if not isinstance(override_body, str) else mock_client(override_body)
    monkeypatch.setattr(processing, "refresh_overrides", lambda repo, manual: real(repo, manual, client=client))
    return api


def test_processing_proposes_overrides(api, repo, layered, monkeypatch):
    # F1 is the new manual's Timesheets passage; B1 the baseline sheet-number passage.
    body = reply(item(firm_excerpt="Timesheets are due every Friday", base_excerpt="A1.01", difference="d"))
    client = processing_client(api, monkeypatch, body)
    manual = upload(client).json()
    client.post(f"/api/manuals/{manual['id']}/process", headers=auth())

    done = client.get(f"/api/manuals/{manual['id']}", headers=auth()).json()
    assert done["status"] == "processed", done["error"]
    assert done["processing_notes"]["baseline_overrides"] == 1
    assert (done["processing_notes"]["input_tokens"], done["processing_notes"]["output_tokens"]) == (2200, 980)
    assert len(repo.select("baseline_overrides", {"manual_id": manual["id"]})) == 1

    # Reprocessing clears the manual's old overrides with its passages.
    client.post(f"/api/manuals/{manual['id']}/process", headers=auth())
    assert len(repo.select("baseline_overrides", {"manual_id": manual["id"]})) == 1


def test_processing_survives_override_detection_failure(api, repo, layered, monkeypatch):
    client = processing_client(api, monkeypatch, error_client(529, "Overloaded"))
    manual = upload(client).json()
    client.post(f"/api/manuals/{manual['id']}/process", headers=auth())

    done = client.get(f"/api/manuals/{manual['id']}", headers=auth()).json()
    assert done["status"] == "processed"
    assert any("override detection failed" in w for w in done["processing_notes"]["warnings"])
    assert repo.select("modules", {"manual_id": manual["id"]})  # drafts kept
