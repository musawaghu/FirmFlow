"""The real token check: every other API test replaces get_token_verifier with a dict lookup.

Supabase's get_user is the only thing faked here, so these tests cover how the
backend turns its answers (a user, no user, nothing, an exception) into
access decisions.
"""

from types import SimpleNamespace

import pytest

from app import auth
from app.auth import get_token_verifier
from app.main import app


class FakeSupabaseAuth:
    """Answers get_user the way supabase_auth does for each kind of token."""

    def __init__(self):
        self.tokens_checked = []

    def get_user(self, token):
        self.tokens_checked.append(token)
        if token == "alex-token":
            return SimpleNamespace(user=SimpleNamespace(id="user-employee-a"))
        if token == "priya-token":
            return SimpleNamespace(user=SimpleNamespace(id="user-admin-a"))
        if token == "no-profile-token":
            return SimpleNamespace(user=SimpleNamespace(id="user-nobody"))
        if token == "deleted-user-token":
            return SimpleNamespace(user=None)
        if token == "empty-response-token":
            return None
        raise RuntimeError("invalid JWT: token is expired")  # supabase_auth raises for bad tokens


@pytest.fixture
def supabase_auth(api, monkeypatch):
    """Use the real verifier, backed by a fake Supabase auth client."""
    fake = FakeSupabaseAuth()
    monkeypatch.setattr(auth, "get_supabase", lambda: SimpleNamespace(auth=fake))
    app.dependency_overrides.pop(get_token_verifier)
    return fake


def get_modules(api, header):
    return api.get("/api/modules", headers={"Authorization": header} if header is not None else {})


def test_valid_token_resolves_to_the_users_own_profile(api, supabase_auth):
    res = get_modules(api, "Bearer alex-token")
    assert res.status_code == 200
    assert res.json()["full_name"] == "Alex Rivera"
    assert supabase_auth.tokens_checked == ["alex-token"]  # the raw token, without the scheme


def test_scheme_is_case_insensitive(api, supabase_auth):
    assert get_modules(api, "bearer alex-token").json()["full_name"] == "Alex Rivera"


@pytest.mark.parametrize("token", ["expired-token", "deleted-user-token", "empty-response-token"])
def test_tokens_supabase_does_not_vouch_for_are_rejected(api, supabase_auth, token):
    res = get_modules(api, f"Bearer {token}")
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid or expired token"


@pytest.mark.parametrize("header", [None, "", "Bearer", "Bearer ", "Basic alex-token", "alex-token"])
def test_malformed_headers_never_reach_supabase(api, supabase_auth, header):
    res = get_modules(api, header)
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing bearer token"
    assert supabase_auth.tokens_checked == []


def test_valid_login_without_a_profile_is_forbidden(api, supabase_auth):
    res = get_modules(api, "Bearer no-profile-token")
    assert res.status_code == 403
    assert res.json()["detail"] == "No FIRM FLOW profile for this user"


def test_employee_token_cannot_use_admin_endpoints(api, supabase_auth):
    res = api.get("/api/admin/progress", headers={"Authorization": "Bearer alex-token"})
    assert res.status_code == 403
    assert res.json()["detail"] == "Admins only"


def test_admin_token_can_use_admin_endpoints(api, supabase_auth):
    res = api.get("/api/admin/progress", headers={"Authorization": "Bearer priya-token"})
    assert res.status_code == 200
    assert [e["full_name"] for e in res.json()["employees"]] == ["Alex Rivera"]


def test_verifier_returns_the_user_id_or_none(monkeypatch):
    fake = FakeSupabaseAuth()
    monkeypatch.setattr(auth, "get_supabase", lambda: SimpleNamespace(auth=fake))
    verify = get_token_verifier()
    assert verify("alex-token") == "user-employee-a"
    assert verify("expired-token") is None
    assert verify("deleted-user-token") is None
    assert verify("empty-response-token") is None
