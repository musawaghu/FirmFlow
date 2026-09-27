"""Shared API test setup: an in-memory database, fake storage, and fake logins."""

import pytest
from fastapi.testclient import TestClient

from app import db
from app.auth import get_token_verifier
from app.main import app
from app.ratelimit import limiter
from tests.fakes import FakeRepo, FakeStorage

FIRM_A = "5e000000-0000-4000-8000-000000000001"
FIRM_B = "5e000000-0000-4000-8000-000000000002"
# bearer token -> auth user id
TOKENS = {
    "admin-a": "user-admin-a",
    "employee-a": "user-employee-a",
    "admin-b": "user-admin-b",
    "ghost": "user-ghost",  # valid login without a profile
}


def auth(token="admin-a"):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def fresh_rate_limits():
    """Rate limit windows are process-wide; start every test with none used."""
    limiter.reset()


@pytest.fixture
def repo():
    r = FakeRepo()
    r.insert("profiles", [
        {"id": "user-admin-a", "firm_id": FIRM_A, "role": "admin", "full_name": "Priya Raman", "email": "priya@a.example"},
        {"id": "user-employee-a", "firm_id": FIRM_A, "role": "employee", "full_name": "Alex Rivera", "email": "alex@a.example"},
        {"id": "user-admin-b", "firm_id": FIRM_B, "role": "admin", "full_name": "Other Admin", "email": "admin@b.example"},
    ])
    return r


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def api(repo, storage):
    app.dependency_overrides[db.get_repo] = lambda: repo
    app.dependency_overrides[db.get_storage] = lambda: storage
    app.dependency_overrides[get_token_verifier] = lambda: TOKENS.get
    yield TestClient(app)
    app.dependency_overrides.clear()
