"""Access control, rate limits, response headers, CORS, upload limits, and Claude call timeouts."""

import io
import zipfile

import httpx2
import pytest
from pydantic import BaseModel

from app import ratelimit
from app.config import Settings
from app.ratelimit import Limit, RateLimiter
from app.routers import admin, baseline, chat, manuals, modules, quiz
from app.auth import get_current_profile, require_admin
from app.services import assistant, llm, parser
from app.services.assistant import AssistantResult, ModuleIndex, ask
from app.services.directory import Directory
from app.services.llm import LLMError, structured_call
from app.services.parser import ParseError, parse_manual
from tests.claude_mock import mock_client, sse
from tests.conftest import auth
from tests.test_manuals_api import docx_bytes

# ---------------------------------------------------------------------------
# Who can call what
# ---------------------------------------------------------------------------

EXPECTED_ACCESS = {
    ("GET", "/api/admin/progress"): "admin",
    ("GET", "/api/admin/failed-questions"): "admin",
    ("GET", "/api/admin/unanswered"): "admin",
    ("GET", "/api/baseline/modules"): "admin",
    ("PATCH", "/api/baseline/modules/{module_id}"): "admin",
    ("PATCH", "/api/overrides/{override_id}"): "admin",
    ("POST", "/api/chat"): "login",
    ("POST", "/api/manuals"): "admin",
    ("GET", "/api/manuals"): "admin",
    ("GET", "/api/manuals/{manual_id}"): "admin",
    ("POST", "/api/manuals/{manual_id}/process"): "admin",
    ("GET", "/api/manuals/{manual_id}/review"): "admin",
    ("GET", "/api/manuals/{manual_id}/issues"): "admin",
    ("GET", "/api/manuals/{manual_id}/overrides"): "admin",
    ("POST", "/api/manuals/{manual_id}/overrides/detect"): "admin",
    ("PATCH", "/api/modules/{module_id}"): "admin",
    ("GET", "/api/modules"): "login",
    ("POST", "/api/modules/{module_id}/progress"): "login",
    ("PATCH", "/api/passages/{passage_id}"): "admin",
    ("POST", "/api/quiz/generate"): "admin",
    ("GET", "/api/quiz/questions"): "admin",
    ("PATCH", "/api/quiz/questions/{question_id}"): "admin",
    ("POST", "/api/quiz/attempts"): "login",
    ("GET", "/api/quiz/attempts/current"): "login",
    ("POST", "/api/quiz/attempts/{attempt_id}/answers"): "login",
}


def _deps(dependant) -> set:
    out = set()
    for sub in dependant.dependencies:
        out.add(sub.call)
        out |= _deps(sub)
    return out


def test_every_route_has_the_expected_access_level():
    """A new route must be added here on purpose, so none ships without a login check."""
    found = {}
    for router in (admin.router, baseline.router, chat.router, manuals.router, modules.router, modules.passages_router, quiz.router):
        for route in router.routes:
            deps = _deps(route.dependant)
            level = "admin" if require_admin in deps else "login" if get_current_profile in deps else "public"
            for method in route.methods:
                found[(method, route.path)] = level
    assert found == EXPECTED_ACCESS


# ---------------------------------------------------------------------------
# Headers and CORS
# ---------------------------------------------------------------------------

def test_security_headers(api):
    res = api.get("/api/modules", headers=auth("employee-a"))
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"
    assert res.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in res.headers["content-security-policy"]
    assert "strict-transport-security" not in res.headers  # development
    assert api.get("/api/modules").headers["cache-control"] == "no-store"  # errors too


def test_cors_allows_only_the_frontend(api):
    preflight = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"}
    ok = api.options("/api/chat", headers={"Origin": "http://localhost:5173", **preflight})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in ok.headers
    other = api.options("/api/chat", headers={"Origin": "https://evil.example", **preflight})
    assert "access-control-allow-origin" not in other.headers


def test_settings_parse_origins_and_environment():
    s = Settings(frontend_origin="http://localhost:5173, https://firmflow.example/", environment="Production")
    assert s.frontend_origins == ["http://localhost:5173", "https://firmflow.example"]
    assert s.is_production
    assert not Settings(environment="development").is_production


# ---------------------------------------------------------------------------
# Rate limits
# ---------------------------------------------------------------------------

def test_limiter_windows_and_all_or_nothing():
    limiter = RateLimiter()
    minute, burst = Limit(2, 60), Limit(3, 3600)
    keys = [(("a", 60), minute), (("a", 3600), burst)]
    assert limiter.check(keys, now=0) is None
    assert limiter.check(keys, now=1) is None
    assert limiter.check(keys, now=2) == pytest.approx(58)  # minute window full
    assert limiter.check(keys, now=61) is None  # first hit expired; the rejected one wasn't recorded
    assert limiter.check(keys, now=62) == pytest.approx(3600 - 62)  # hour window full


def test_per_user_limit_on_chat(api, monkeypatch):
    monkeypatch.setitem(ratelimit.LIMITS, "chat", [Limit(2, 60)])
    monkeypatch.setattr(chat, "ask", lambda *a, **k: AssistantResult("other", "ok", [], [], False))
    for _ in range(2):
        assert api.post("/api/chat", json={"question": "hi"}, headers=auth("employee-a")).status_code == 200
    res = api.post("/api/chat", json={"question": "hi"}, headers=auth("employee-a"))
    assert res.status_code == 429
    assert int(res.headers["retry-after"]) >= 1
    assert "Too many requests" in res.json()["detail"]
    # Someone else isn't affected.
    assert api.post("/api/chat", json={"question": "hi"}, headers=auth("admin-a")).status_code == 200


def test_per_firm_limit_on_uploads(api, monkeypatch):
    monkeypatch.setitem(ratelimit.LIMITS, "upload", [Limit(1, 3600, "firm")])
    upload = lambda token: api.post("/api/manuals", files={"file": ("x.txt", b"hi")}, headers=auth(token))  # noqa: E731
    assert upload("admin-a").status_code == 415
    assert upload("admin-a").status_code == 429
    assert upload("admin-b").status_code == 415  # another firm


def test_per_ip_limit(api, monkeypatch):
    monkeypatch.setattr(ratelimit, "IP_LIMIT", Limit(3, 60, "ip"))
    codes = [api.get("/api/modules", headers=auth("employee-a")).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    assert api.get("/api/health").status_code == 200  # health checks are exempt


def test_limits_can_be_turned_off(api, monkeypatch):
    monkeypatch.setattr(ratelimit, "IP_LIMIT", Limit(1, 60, "ip"))
    monkeypatch.setattr(ratelimit, "get_settings", lambda: Settings(rate_limits_enabled=False))
    assert [api.get("/api/modules", headers=auth("employee-a")).status_code for _ in range(3)] == [200, 200, 200]


# ---------------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------------

def test_docx_that_unpacks_too_large_is_refused(monkeypatch):
    monkeypatch.setattr(parser, "MAX_DOCX_UNZIPPED_BYTES", 1000)
    with pytest.raises(ParseError, match="too large"):
        parse_manual(docx_bytes(), "docx")


def test_docx_with_too_many_entries_is_refused(monkeypatch):
    monkeypatch.setattr(parser, "MAX_DOCX_ENTRIES", 1)
    with pytest.raises(ParseError, match="too large"):
        parse_manual(docx_bytes(), "docx")


def test_damaged_docx_is_refused():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("hello.txt", "not a document")
    with pytest.raises(ParseError):
        parse_manual(buf.getvalue(), "docx")
    with pytest.raises(ParseError, match="damaged"):
        parse_manual(b"PK\x03\x04 garbage", "docx")


# ---------------------------------------------------------------------------
# Claude call timeouts
# ---------------------------------------------------------------------------

class Answer(BaseModel):
    text: str


def call(client, **kw):
    return structured_call(system="s", user="u", output_format=Answer, max_tokens=100, client=client, **kw)


def test_client_has_bounded_timeouts_and_retries():
    client = llm.claude_client()
    assert client.max_retries == llm.MAX_RETRIES == 1
    assert (client.timeout.read, client.timeout.connect) == (llm.READ_TIMEOUT, llm.CONNECT_TIMEOUT)


def test_structured_call_gives_up_after_its_deadline(monkeypatch):
    clock = iter([0.0, 5.0, 500.0, 500.0, 500.0, 500.0, 500.0, 500.0, 500.0])
    monkeypatch.setattr(llm.time, "monotonic", lambda: next(clock))
    with pytest.raises(LLMError, match="longer than 60 seconds"):
        call(mock_client(sse({"text": "hi"})), deadline=60)


def test_structured_call_within_its_deadline():
    parsed, _ = call(mock_client(sse({"text": "hi"})), deadline=60)
    assert parsed.text == "hi"


def test_stalled_connection_becomes_a_clear_error():
    import anthropic

    def handler(request):
        raise httpx2.ReadTimeout("stalled", request=request)

    client = anthropic.Anthropic(api_key="test", max_retries=0,
                                 http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    with pytest.raises(LLMError, match="stopped responding"):
        call(client)


def test_assistant_falls_back_when_out_of_time(repo, monkeypatch):
    from tests.directory_seed import seed_directory

    seed_directory(repo)
    directory = Directory.load(repo, "5e000000-0000-4000-8000-000000000001")
    clock = iter([0.0, 1000.0])
    monkeypatch.setattr(assistant.time, "monotonic", lambda: next(clock))
    result = ask("Who handles payroll?", directory=directory, index=ModuleIndex.build([], []), employee_name="Alex",
                 client=mock_client("unused"))
    assert result.used_fallback is True
