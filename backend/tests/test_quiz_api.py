import json

import pytest

from app.routers import quiz as quiz_router
from app.services import quiz as quiz_service
from tests.claude_mock import error_client, mock_client, sse
from tests.conftest import FIRM_A, auth

DETACH_TEXT = (
    'Do NOT copy the central file in File Explorer. Check "Detach from Central", choose '
    '"Detach and preserve worksets", and save to the Sandbox folder. Synchronize at least every hour.'
)


def mc(passage, prompt, correct=1):
    return {"passage_id": passage, "type": "multiple_choice", "prompt": prompt,
            "choices": ["Copy it in File Explorer", "Detach from Central", "Email it", "Rename it"],
            "correct_choice": correct, "rubric": None, "explanation": "The manual says to detach from central."}


def scenario(passage, prompt):
    return {"passage_id": passage, "type": "scenario", "prompt": prompt, "choices": None, "correct_choice": None,
            "rubric": "Must say to open with Detach from Central and save to Sandbox; copying in File Explorer is wrong.",
            "explanation": "Detaching keeps the central model safe."}


GENERATED = {"questions": [
    mc("P1", "How do you make a test copy?"),
    mc("P2", "How often do you sync?", correct=2),
    mc("P1", "Where do test copies go?", correct=3),
    mc("P2", "What do you sync with?", correct=0),
    scenario("P1", "You need a copy of the central model to test an option. What do you do?"),
    scenario("P2", "You're about to leave for the day. What do you do with your model?"),
]}


@pytest.fixture
def seeded(repo):
    """An approved BIM module with two critical passages, one plain passage, and a draft module."""
    manual = repo.insert("manuals", [{"firm_id": FIRM_A, "title": "Handbook", "file_path": "x", "file_type": "pdf", "status": "processed"}])[0]
    section = repo.insert("source_sections", [{"manual_id": manual["id"], "ordinal": 8, "heading": "4.2 Making a test copy",
                                               "content": DETACH_TEXT, "page_start": 5, "page_end": 5}])[0]
    bim, draft = repo.insert("modules", [
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "How to Use BIM", "ordinal": 0, "priority": "day_1", "status": "approved"},
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "Draft Module", "ordinal": 1, "priority": "day_1", "is_required": False},
    ])
    detach, sync, plain, draft_passage = repo.insert("module_passages", [
        {"module_id": bim["id"], "source_section_id": section["id"], "ordinal": 0, "heading": "Test copies",
         "content": "Open the central model with Detach from Central.", "kind": "text", "is_critical": True, "grounding_ok": True},
        {"module_id": bim["id"], "source_section_id": section["id"], "ordinal": 1, "heading": "Syncing",
         "content": "Synchronize at least every hour.", "kind": "text", "is_critical": True, "grounding_ok": True},
        {"module_id": bim["id"], "source_section_id": section["id"], "ordinal": 2, "heading": None,
         "content": "Save to the Sandbox folder.", "kind": "text", "grounding_ok": True},
        {"module_id": draft["id"], "source_section_id": section["id"], "ordinal": 0, "heading": None,
         "content": "DRAFT-ONLY TEXT", "kind": "text", "is_critical": True, "grounding_ok": True},
    ])
    return {"bim": bim, "detach": detach, "sync": sync, "plain": plain, "draft_passage": draft_passage}


@pytest.fixture
def claude(monkeypatch):
    """Controls what the mocked model returns for generation and grading."""
    state = {"generate": GENERATED, "grade": {"is_correct": True, "feedback": "Right: detaching keeps the central model safe."},
             "requests": [], "fail": False}

    def client(payload):
        return error_client(529) if state["fail"] else mock_client(sse(payload), state["requests"])

    real_generate, real_grade = quiz_service.generate_questions, quiz_service.grade_scenario
    monkeypatch.setattr(quiz_router, "generate_questions", lambda passages: real_generate(passages, client=client(state["generate"])))
    monkeypatch.setattr(quiz_router, "grade_scenario", lambda **kw: real_grade(**kw, client=client(state["grade"])))
    return state


def generate(api, token="admin-a"):
    return api.post("/api/quiz/generate", headers=auth(token))


def approve_all(api, repo):
    for q in repo.select("quiz_questions", {"status": "draft"}):
        assert api.patch(f"/api/quiz/questions/{q['id']}", json={"status": "approved"}, headers=auth()).status_code == 200


def complete_modules(api, seeded, token="employee-a"):
    res = api.post(f"/api/modules/{seeded['bim']['id']}/progress", json={"status": "completed"}, headers=auth(token))
    assert res.status_code == 200


def start(api, token="employee-a"):
    return api.post("/api/quiz/attempts", headers=auth(token))


def answer(api, attempt_id, question_id, token="employee-a", **body):
    return api.post(f"/api/quiz/attempts/{attempt_id}/answers", json={"question_id": question_id, **body}, headers=auth(token))


def key(repo, question_id):
    return repo.select_one("quiz_questions", {"id": question_id})


# ---------------------------------------------------------------------------
# Generation and the question bank
# ---------------------------------------------------------------------------

def test_generate_drafts_from_critical_passages(api, repo, seeded, claude):
    res = generate(api)
    assert res.status_code == 201, res.text
    body = res.json()
    assert len(body["questions"]) == 6 and body["warnings"] == []
    first = body["questions"][0]
    assert (first["passage_id"], first["status"], first["correct_choice"]) == (seeded["detach"]["id"], "draft", 1)
    assert first["link"] == {"module_id": seeded["bim"]["id"], "module_title": "How to Use BIM",
                             "passage_id": seeded["detach"]["id"], "passage_heading": "Test copies"}

    prompt = json.loads(claude["requests"][0].content)["messages"][0]["content"]
    assert "Detach from Central" in prompt
    assert "DRAFT-ONLY TEXT" not in prompt  # draft modules are never quizzed
    assert "Save to the Sandbox folder." not in prompt  # nor passages not marked critical


def test_regenerating_replaces_drafts_until_approved(api, repo, seeded, claude):
    generate(api)
    generate(api)
    assert len(repo.select("quiz_questions")) == 6

    approve_all(api, repo)
    res = generate(api)
    assert res.status_code == 409 and "already approved" in res.json()["detail"]


def test_generate_needs_critical_passages(api, repo, seeded, claude):
    for p in (seeded["detach"], seeded["sync"]):
        repo.update("module_passages", p["id"], {"is_critical": False})
    assert generate(api).status_code == 409


def test_generate_model_failure(api, seeded, claude):
    claude["fail"] = True
    res = generate(api)
    assert res.status_code == 503 and "529" in res.json()["detail"]


def test_bank_is_admin_only(api, seeded, claude):
    assert generate(api, token="employee-a").status_code == 403
    assert api.get("/api/quiz/questions", headers=auth("employee-a")).status_code == 403


def test_edit_and_approve_questions(api, repo, seeded, claude):
    q = generate(api).json()["questions"][0]
    url = f"/api/quiz/questions/{q['id']}"

    res = api.patch(url, json={"prompt": "How do you make a safe test copy?", "correct_choice": 1}, headers=auth())
    assert res.json()["prompt"] == "How do you make a safe test copy?"
    assert api.patch(url, json={"correct_choice": 7}, headers=auth()).status_code == 422
    assert api.patch(url, json={"choices": ["A", "A", "B", "C"]}, headers=auth()).status_code == 422

    assert api.patch(url, json={"status": "approved"}, headers=auth()).json()["status"] == "approved"
    assert api.patch(url, json={"prompt": "Changed"}, headers=auth()).status_code == 409
    res = api.patch(url, json={"status": "draft", "prompt": "Changed"}, headers=auth())
    assert (res.json()["status"], res.json()["prompt"]) == ("draft", "Changed")

    listed = api.get("/api/quiz/questions?status=draft", headers=auth()).json()
    assert len(listed) == 6


def test_question_from_ineligible_passage_cannot_be_approved(api, repo, seeded, claude):
    q = generate(api).json()["questions"][0]
    repo.update("module_passages", seeded["detach"]["id"], {"is_critical": False})
    res = api.patch(f"/api/quiz/questions/{q['id']}", json={"status": "approved"}, headers=auth())
    assert res.status_code == 409


def test_other_firms_cannot_touch_questions(api, repo, seeded, claude):
    q = generate(api).json()["questions"][0]
    assert api.patch(f"/api/quiz/questions/{q['id']}", json={"status": "approved"}, headers=auth("admin-b")).status_code == 404
    assert api.get("/api/quiz/questions", headers=auth("admin-b")).json() == []


# ---------------------------------------------------------------------------
# Attempts
# ---------------------------------------------------------------------------

@pytest.fixture
def ready(api, repo, seeded, claude):
    """Approved question bank and an employee who finished the required modules."""
    generate(api)
    approve_all(api, repo)
    complete_modules(api, seeded)
    return seeded


def test_check_is_locked_until_required_modules_are_done(api, repo, seeded, claude):
    generate(api)
    approve_all(api, repo)
    res = start(api)
    assert res.status_code == 403 and "required modules" in res.json()["detail"]


def test_check_needs_an_approved_bank(api, repo, seeded, claude):
    complete_modules(api, seeded)
    generate(api)  # drafts only
    assert start(api).status_code == 409


def test_start_and_resume_attempt(api, repo, ready):
    res = start(api)
    assert res.status_code == 201
    attempt = res.json()
    assert attempt["status"] == "in_progress" and len(attempt["questions"]) == 6
    types = [q["type"] for q in attempt["questions"]]
    assert types[-2:] == ["scenario", "scenario"]  # free text comes last
    q = attempt["questions"][0]
    assert set(q) == {"id", "type", "prompt", "choices", "state", "tries", "link"}  # no answer key
    assert (q["state"], q["tries"], q["link"]) == ("unanswered", 0, None)

    again = start(api)
    assert again.status_code == 200 and again.json()["id"] == attempt["id"]
    assert api.get("/api/quiz/attempts/current", headers=auth("employee-a")).json()["id"] == attempt["id"]


def test_questions_from_unapproved_modules_are_skipped(api, repo, ready):
    for q in repo.select("quiz_questions", {"passage_id": ready["sync"]["id"]}):
        repo.update("quiz_questions", q["id"], {"passage_id": ready["draft_passage"]["id"]})
    attempt = start(api).json()
    assert {key(repo, q["id"])["passage_id"] for q in attempt["questions"]} == {ready["detach"]["id"]}


def test_multiple_choice_miss_then_retry(api, repo, ready):
    attempt = start(api).json()
    q = next(q for q in attempt["questions"] if q["type"] == "multiple_choice")
    correct = key(repo, q["id"])["correct_choice"]
    wrong = (correct + 1) % 4

    res = answer(api, attempt["id"], q["id"], selected_choice=wrong).json()
    assert res["is_correct"] is False and res["try_number"] == 1
    assert "detach from central" not in res["feedback"].lower()  # the answer isn't revealed on a miss
    assert "Review “" in res["feedback"] and "in How to Use BIM" in res["feedback"]
    assert res["link"]["module_title"] == "How to Use BIM"
    missed = next(x for x in res["attempt"]["questions"] if x["id"] == q["id"])
    assert (missed["state"], missed["tries"]) == ("missed", 1) and missed["link"]

    res = answer(api, attempt["id"], q["id"], selected_choice=correct).json()
    assert res["is_correct"] is True and res["try_number"] == 2 and res["link"] is None
    assert res["feedback"] == "The manual says to detach from central."

    assert answer(api, attempt["id"], q["id"], selected_choice=correct).status_code == 409
    assert answer(api, attempt["id"], q["id"], selected_choice=9).status_code == 409  # already correct beats validation


def test_invalid_answers_are_rejected(api, repo, ready):
    attempt = start(api).json()
    mc_q = next(q for q in attempt["questions"] if q["type"] == "multiple_choice")
    sc_q = next(q for q in attempt["questions"] if q["type"] == "scenario")
    assert answer(api, attempt["id"], mc_q["id"], selected_choice=4).status_code == 422
    assert answer(api, attempt["id"], mc_q["id"]).status_code == 422
    assert answer(api, attempt["id"], sc_q["id"], answer_text="   ").status_code == 422
    assert answer(api, attempt["id"], sc_q["id"], answer_text="x" * 2001).status_code == 422
    assert answer(api, attempt["id"], "not-in-attempt", selected_choice=0).status_code == 404
    assert repo.select("quiz_answers") == []


def test_scenario_grading(api, repo, ready, claude):
    attempt = start(api).json()
    q = next(q for q in attempt["questions"] if q["type"] == "scenario")

    claude["grade"] = {"is_correct": False, "feedback": "Copying the file in File Explorer can corrupt the model."}
    res = answer(api, attempt["id"], q["id"], answer_text="I'd copy the file in File Explorer.").json()
    assert res["is_correct"] is False
    assert res["feedback"].startswith("Copying the file in File Explorer can corrupt the model. Review “")

    grade_request = json.loads(claude["requests"][-1].content)["messages"][0]["content"]
    assert "<answer>\nI'd copy the file in File Explorer.\n</answer>" in grade_request
    assert DETACH_TEXT in grade_request

    claude["grade"] = {"is_correct": True, "feedback": "Right: detaching keeps the central model safe."}
    res = answer(api, attempt["id"], q["id"], answer_text="Open it with Detach from Central and save to Sandbox.").json()
    assert res["is_correct"] is True and res["try_number"] == 2
    stored = repo.select("quiz_answers", {"question_id": q["id"]})
    assert [a["answer_text"] for a in stored] == ["I'd copy the file in File Explorer.", "Open it with Detach from Central and save to Sandbox."]


def test_grader_outage_records_nothing(api, repo, ready, claude):
    attempt = start(api).json()
    q = next(q for q in attempt["questions"] if q["type"] == "scenario")
    claude["fail"] = True
    assert answer(api, attempt["id"], q["id"], answer_text="Detach from Central.").status_code == 503
    assert repo.select("quiz_answers") == []


def test_attempt_completes_when_everything_is_correct(api, repo, ready, claude):
    attempt = start(api).json()
    questions = attempt["questions"]
    first_mc = next(q for q in questions if q["type"] == "multiple_choice")

    # Miss one question on the first try, then answer everything correctly.
    wrong = (key(repo, first_mc["id"])["correct_choice"] + 1) % 4
    answer(api, attempt["id"], first_mc["id"], selected_choice=wrong)
    for q in questions:
        body = {"selected_choice": key(repo, q["id"])["correct_choice"]} if q["type"] == "multiple_choice" else {"answer_text": "Detach from Central."}
        last = answer(api, attempt["id"], q["id"], **body).json()

    done = last["attempt"]
    assert done["status"] == "completed" and done["completed_at"]
    assert done["score"] == round(5 / 6 * 100, 2)
    assert answer(api, attempt["id"], first_mc["id"], selected_choice=0).status_code == 409

    # A new attempt can be started after completing one.
    assert start(api).json()["id"] != attempt["id"]


def test_attempts_are_private(api, repo, ready):
    attempt = start(api).json()
    q = attempt["questions"][0]
    assert answer(api, attempt["id"], q["id"], token="admin-a", selected_choice=0).status_code == 404
    assert api.get("/api/quiz/attempts/current", headers=auth("admin-b")).status_code == 404


# ---------------------------------------------------------------------------
# Admin: most-failed questions
# ---------------------------------------------------------------------------

def test_failed_questions_ranking(api, repo, ready, claude):
    attempt = start(api).json()
    mcs = [q for q in attempt["questions"] if q["type"] == "multiple_choice"]
    missed, passed = mcs[0], mcs[1]
    answer(api, attempt["id"], missed["id"], selected_choice=(key(repo, missed["id"])["correct_choice"] + 1) % 4)
    answer(api, attempt["id"], missed["id"], selected_choice=key(repo, missed["id"])["correct_choice"])  # retries don't count
    answer(api, attempt["id"], passed["id"], selected_choice=key(repo, passed["id"])["correct_choice"])

    rows = api.get("/api/admin/failed-questions", headers=auth()).json()
    assert [(r["question_id"], r["first_tries"], r["first_try_misses"], r["miss_rate"]) for r in rows] == [
        (missed["id"], 1, 1, 1.0),
        (passed["id"], 1, 0, 0.0),
    ]
    assert rows[0]["link"]["module_title"] == "How to Use BIM"
    assert api.get("/api/admin/failed-questions", headers=auth("employee-a")).status_code == 403
    assert api.get("/api/admin/failed-questions", headers=auth("admin-b")).json() == []
