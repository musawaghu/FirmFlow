import json
from datetime import date

import pytest

from app.routers import chat as chat_router
from app.services import assistant
from app.services.assistant import MAX_TURNS, ModuleIndex, ask
from app.services.directory import Directory
from tests.claude_mock import error_client, message, mock_client, text_json, tool_use
from tests.conftest import FIRM_A, auth
from tests.directory_seed import seed_directory

THURSDAY = date(2026, 10, 1)

MODULES = [
    {"id": "mod-pto", "title": "PTO", "ordinal": 4},
    {"id": "mod-bim", "title": "How to Use BIM", "ordinal": 3},
]
PASSAGES = [
    {"id": "pas-pto-1", "module_id": "mod-pto", "ordinal": 0, "heading": "Requesting time off",
     "content": "Request PTO in the HR portal and talk to your Project Manager first."},
    {"id": "pas-bim-1", "module_id": "mod-bim", "ordinal": 0, "heading": "Test copies",
     "content": "Open the central model with Detach from Central."},
]


@pytest.fixture
def directory(repo):
    ids = seed_directory(repo)
    d = Directory.load(repo, FIRM_A)
    d.ids = ids
    return d


@pytest.fixture
def index():
    return ModuleIndex.build(MODULES, PASSAGES)


def final(intent="who_can_help", answered=True, answer="Here's who can help.", passages=(), people=(),
          subject="Quick question", body="Could you help me with this?"):
    return message(text_json({
        "intent": intent, "answered": answered, "answer": answer, "passage_ids": list(passages),
        "person_ids": list(people), "email_subject": subject if people else None, "email_body": body if people else None,
    }))


def calls(*tools):
    return message(*[tool_use(name, args, id=f"toolu_{n}") for n, (name, args) in enumerate(tools)], stop_reason="tool_use")


def run(directory, index, replies, requests=None, question="Who can help?"):
    return ask(question, directory=directory, index=index, employee_name="Alex Rivera", today=THURSDAY,
               client=mock_client(replies, requests if requests is not None else []))


def sid(directory, who):
    return directory.short_ids[directory.ids[who]]


# ---------------------------------------------------------------------------
# ask()
# ---------------------------------------------------------------------------

def test_index_orders_modules_and_renders_ids(index):
    assert [m["title"] for _, m in index.passages.values()] == ["How to Use BIM", "PTO"]
    rendered = index.render()
    assert '<module title="How to Use BIM">\n<passage id="p1" heading="Test copies">' in rendered
    assert index.link("p2") == {"module_id": "mod-pto", "module_title": "PTO", "passage_id": "pas-pto-1",
                                "passage_heading": "Requesting time off"}


def test_payroll_question_routes_privately_with_backup(directory, index):
    requests = []
    result = run(directory, index, [
        calls(("find_people_for_topic", {"topic": "payroll"})),
        final(intent="personal_matter", answer="Payroll handles this; reach out to them directly.",
              people=[sid(directory, "tom")], subject="Payroll question", body="I have a question about my paycheck."),
    ], requests, question="I had a problem with my payroll, who can I ask?")

    assert (result.intent, result.used_fallback, result.personal_topic) == ("personal_matter", False, "payroll")
    card = result.contacts[0]
    assert (card["name"], card["email"], card["is_in_today"]) == ("Tom Brennan", "tom.brennan@studiomeridian.example", False)
    assert card["reason"].startswith("Paychecks")
    assert card["backup"]["name"] == "Grace Liu" and card["backup"]["is_in_today"] is True
    assert "subject=Payroll%20question" in card["mailto"]

    first, second = (json.loads(r.content) for r in requests)
    assert first["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Open the central model with Detach from Central." in first["system"][0]["text"]
    assert first["messages"][0]["content"] == "<question>\nI had a problem with my payroll, who can I ask?\n</question>"
    topic_tool = next(t for t in first["tools"] if t["name"] == "find_people_for_topic")
    assert topic_tool["input_schema"]["properties"]["topic"]["enum"] == ["bim", "office", "payroll"]
    assert topic_tool["strict"] is True
    assert first["output_config"]["effort"] == "medium" and first["fallbacks"] == "default"

    tool_result = second["messages"][2]["content"][0]
    assert tool_result["tool_use_id"] == "toolu_0" and tool_result["is_error"] is False
    payload = json.loads(tool_result["content"])
    assert payload["is_personal"] is True and [p["name"] for p in payload["people"]] == ["Tom Brennan", "Grace Liu"]


def test_project_role_question(directory, index):
    result = run(directory, index, [
        calls(("find_project_role", {"project": "Riverside Library", "role": "design_manager"})),
        final(people=[sid(directory, "rachel")]),
    ], question="Who is the design manager for Riverside Library?")
    assert [c["name"] for c in result.contacts] == ["Rachel Adeyemi"]
    assert result.contacts[0]["reason"] == "Design manager, Riverside Library (RL-2301)"
    assert result.contacts[0]["backup"] is None  # she's in


def test_where_is_question_links_to_passage(directory, index):
    result = run(directory, index, [
        final(intent="where_is", answer="Request PTO in the HR portal after talking to your PM.", passages=["p2"]),
    ], question="Where is the PTO policy?")
    assert (result.intent, result.used_fallback, result.contacts) == ("where_is", False, [])
    assert result.links == [index.link("p2")]


def test_parallel_tool_calls_share_one_result_message(directory, index):
    requests = []
    run(directory, index, [
        calls(("search_people", {"name": "Samir"}), ("find_people_for_topic", {"topic": "bim"})),
        final(people=[sid(directory, "samir")]),
    ], requests)
    results = json.loads(requests[1].content)["messages"][2]["content"]
    assert [r["tool_use_id"] for r in results] == ["toolu_0", "toolu_1"]


def test_tool_errors_are_reported_to_the_model(directory, index):
    requests = []
    run(directory, index, [
        calls(("find_project_role", {"project": "Moon Base", "role": "design_manager"})),
        final(answered=False, answer="I couldn't find that project."),
    ], requests)
    result_block = json.loads(requests[1].content)["messages"][2]["content"][0]
    assert result_block["is_error"] is True
    assert "Riverside Library (RL-2301)" in result_block["content"]  # lists real projects to retry with


def test_person_not_returned_by_a_tool_is_never_shown(directory, index):
    # The model cites Samir without looking him up, and an id that doesn't exist.
    result = run(directory, index, [final(people=[sid(directory, "samir"), "E99"])])
    assert result.used_fallback is True
    assert [c["name"] for c in result.contacts] == ["Priya Raman"]  # the firm's default contact
    assert any("E99" in n for n in result.notes) and any(sid(directory, "samir") in n for n in result.notes)


def test_unanswered_routes_to_default_contact(directory, index):
    result = run(directory, index, [final(intent="other", answered=False, answer="Maybe try Bob?", passages=["p1"])],
                 question="Who fixes the espresso machine?")
    assert result.used_fallback is True
    assert "Bob" not in result.answer and "Office Manager" in result.answer
    assert result.contacts[0]["name"] == "Priya Raman" and result.contacts[0]["reason"].startswith("Office Manager")
    assert result.links == [index.link("p1")]  # valid links still help


def test_who_question_without_a_person_falls_back(directory, index):
    result = run(directory, index, [final(intent="who_can_help", passages=["p1"])])
    assert result.used_fallback is True


def test_personal_matter_that_falls_back_is_still_redacted(directory, index):
    result = run(directory, index, [
        calls(("find_people_for_topic", {"topic": "payroll"})),
        final(intent="personal_matter", answered=False),
    ])
    assert result.used_fallback is True and result.personal_topic == "payroll"


def test_invented_passage_ids_are_dropped(directory, index):
    result = run(directory, index, [final(intent="where_is", passages=["p2", "p42"])])
    assert [link["passage_id"] for link in result.links] == ["pas-pto-1"]
    assert any("p42" in n for n in result.notes)


def test_emails_in_answer_text_are_removed(directory, index):
    result = run(directory, index, [
        calls(("search_people", {"name": "Samir"})),
        final(answer="Email samir.haddad@studiomeridian.example about BIM.", people=[sid(directory, "samir")]),
    ])
    assert result.answer == "Email about BIM."
    assert result.contacts[0]["email"] == "samir.haddad@studiomeridian.example"  # from the directory row


def test_tool_loop_is_capped(directory, index):
    requests = []
    result = run(directory, index, calls(("search_people", {"name": "Samir"})), requests)
    assert len(requests) == MAX_TURNS
    assert result.used_fallback is True and result.notes == ["Too many tool rounds"]


def test_api_outage_falls_back(directory, index):
    result = ask("Who can help?", directory=directory, index=index, employee_name="Alex", today=THURSDAY, client=error_client(529))
    assert result.used_fallback is True
    assert "isn't available right now" in result.answer and result.contacts[0]["name"] == "Priya Raman"


def test_refusal_falls_back(directory, index):
    result = run(directory, index, message(text_json({}), stop_reason="refusal"))
    assert result.used_fallback is True


def test_firm_without_default_contact(directory, index, repo):
    directory.firm["default_contact_id"] = None
    result = run(directory, index, [final(answered=False)])
    assert result.contacts == [] and "office manager or HR" in result.answer


# ---------------------------------------------------------------------------
# POST /api/chat and GET /api/admin/unanswered
# ---------------------------------------------------------------------------

@pytest.fixture
def chat_api(api, repo, monkeypatch):
    ids = seed_directory(repo)
    module = repo.insert("modules", [{"firm_id": FIRM_A, "title": "PTO", "ordinal": 0, "priority": "week_1", "status": "approved"}])[0]
    draft = repo.insert("modules", [{"firm_id": FIRM_A, "title": "Draft", "ordinal": 1, "priority": "later"}])[0]
    repo.insert("module_passages", [
        {"module_id": module["id"], "source_section_id": "s", "ordinal": 0, "heading": "Requesting time off",
         "content": "Request PTO in the HR portal.", "kind": "text"},
        {"module_id": draft["id"], "source_section_id": "s", "ordinal": 0, "heading": None,
         "content": "DRAFT-ONLY TEXT", "kind": "text"},
    ])
    state = {"replies": [], "requests": []}
    real_ask = assistant.ask
    monkeypatch.setattr(chat_router, "ask", lambda q, **kw: real_ask(
        q, **kw, today=THURSDAY, client=mock_client(state["replies"], state["requests"])))
    state["ids"] = ids
    return state


def post(api, question, token="employee-a"):
    return api.post("/api/chat", json={"question": question}, headers=auth(token))


def test_chat_endpoint_answers_and_logs(api, repo, chat_api):
    chat_api["replies"] = [final(intent="where_is", answer="Request PTO in the HR portal.", passages=["p1"])]
    res = post(api, "  Where is the PTO policy? ")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["links"][0]["passage_heading"] == "Requesting time off" and body["used_fallback"] is False

    system = json.loads(chat_api["requests"][0].content)["system"][0]["text"]
    assert "Request PTO in the HR portal." in system and "DRAFT-ONLY TEXT" not in system

    log = repo.select("chat_logs")[0]
    assert (log["question"], log["intent"], log["used_fallback"], log["profile_id"]) == (
        "Where is the PTO policy?", "where_is", False, "user-employee-a")
    assert log["matched_passage_id"] == body["links"][0]["passage_id"]


def test_chat_logs_personal_matters_without_details(api, repo, chat_api):
    tom = Directory.load(repo, FIRM_A).short_ids[chat_api["ids"]["tom"]]
    chat_api["replies"] = [calls(("find_people_for_topic", {"topic": "payroll"})), final(intent="personal_matter", people=[tom])]
    body = post(api, "My paycheck was short $212 because of my garnishment, who do I ask?").json()
    assert body["contacts"][0]["name"] == "Tom Brennan" and body["contacts"][0]["backup"]["name"] == "Grace Liu"

    log = repo.select("chat_logs")[0]
    assert log["question"] == "(personal matter: payroll)"
    assert log["matched_person_id"] == chat_api["ids"]["tom"]


def test_unanswered_questions_for_admin(api, repo, chat_api):
    chat_api["replies"] = [final(intent="other", answered=False)]
    post(api, "Who fixes the espresso machine?")
    chat_api["replies"] = [final(intent="where_is", passages=["p1"])]
    post(api, "Where is the PTO policy?")

    rows = api.get("/api/admin/unanswered", headers=auth()).json()
    assert [r["question"] for r in rows] == ["Who fixes the espresso machine?"]
    assert repo.select("chat_logs", {"used_fallback": True})[0]["matched_person_id"] is None
    assert api.get("/api/admin/unanswered", headers=auth("employee-a")).status_code == 403
    assert api.get("/api/admin/unanswered", headers=auth("admin-b")).json() == []


@pytest.mark.parametrize("question", ["", "x" * 501])
def test_chat_validates_question(api, chat_api, question):
    assert post(api, question).status_code == 422
