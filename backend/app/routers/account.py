"""Who is signed in: the frontend uses this after login to pick the admin or employee view."""

from fastapi import APIRouter, Depends

from app.auth import Profile, get_current_profile
from app.db import Repo, get_repo
from app.schemas import MeOut

router = APIRouter(prefix="/api/me", tags=["account"])


@router.get("", response_model=MeOut)
def me(profile: Profile = Depends(get_current_profile), repo: Repo = Depends(get_repo)):
    firm = repo.select_one("firms", {"id": profile.firm_id})
    return {**profile.model_dump(), "firm_name": firm["name"] if firm else None}
