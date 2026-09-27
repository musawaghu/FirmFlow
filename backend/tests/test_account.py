"""GET /api/me: who is signed in, so the frontend can open the right view."""

from tests.conftest import FIRM_A, auth


def test_me_returns_role_and_firm(api, repo):
    repo.insert("firms", [{"id": FIRM_A, "name": "Studio Meridian Architects"}])
    assert api.get("/api/me", headers=auth("admin-a")).json() == {
        "id": "user-admin-a", "full_name": "Priya Raman", "email": "priya@a.example",
        "role": "admin", "firm_id": FIRM_A, "firm_name": "Studio Meridian Architects",
    }
    employee = api.get("/api/me", headers=auth("employee-a")).json()
    assert (employee["role"], employee["full_name"]) == ("employee", "Alex Rivera")


def test_me_needs_a_profile(api):
    assert api.get("/api/me").status_code == 401
    assert api.get("/api/me", headers=auth("ghost")).status_code == 403
