"""Request authentication.

The frontend logs in with Supabase Auth and sends the access token as
`Authorization: Bearer <token>`. The backend asks Supabase who the token
belongs to, then loads that user's profile for their firm and role.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.db import Repo, get_repo, get_supabase


class Profile(BaseModel):
    id: str
    firm_id: str
    person_id: str | None = None
    role: str
    full_name: str
    email: str


def get_token_verifier() -> Callable[[str], str | None]:
    """Returns a function that maps an access token to a user id, or None if invalid."""
    client = get_supabase()

    def verify(token: str) -> str | None:
        try:
            response = client.auth.get_user(token)
        except Exception:  # supabase_auth raises several error types for bad tokens
            return None
        return response.user.id if response and response.user else None

    return verify


def get_current_profile(
    authorization: str | None = Header(default=None),
    repo: Repo = Depends(get_repo),
    verify: Callable[[str], str | None] = Depends(get_token_verifier),
) -> Profile:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    user_id = verify(token)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    row = repo.select_one("profiles", {"id": user_id})
    if row is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No FIRM FLOW profile for this user")
    return Profile(**{k: row.get(k) for k in Profile.model_fields})


def require_admin(profile: Profile = Depends(get_current_profile)) -> Profile:
    if profile.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only")
    return profile
