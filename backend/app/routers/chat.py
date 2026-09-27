"""The "Who do I ask?" assistant endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import Profile, get_current_profile
from app.db import Repo, get_repo
from app.ratelimit import rate_limit
from app.schemas import ChatOut
from app.services.assistant import ModuleIndex, ask
from app.services.content import firm_content
from app.services.directory import Directory

router = APIRouter(prefix="/api/chat", tags=["assistant"])


class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@router.post("", response_model=ChatOut, dependencies=[Depends(rate_limit("chat"))])
def chat(body: ChatIn, profile: Profile = Depends(get_current_profile), repo: Repo = Depends(get_repo)):
    """Answer a "where is" or "who can help" question with module links and contact cards."""
    directory = Directory.load(repo, profile.firm_id)
    content = firm_content(repo, profile.firm_id)
    # Where the firm overrides a baseline passage, the firm's own passage is already in the index.
    passages = [p for p in content.passages if not p["overridden_by_firm"]]
    result = ask(body.question.strip(), directory=directory, index=ModuleIndex.build(content.modules, passages), employee_name=profile.full_name)

    repo.insert("chat_logs", [{
        "firm_id": profile.firm_id,
        "profile_id": profile.id,
        # Personal matters are routed, not recorded.
        "question": f"(personal matter: {result.personal_topic})" if result.personal_topic else body.question.strip(),
        "answer": result.answer,
        "intent": result.intent,
        "matched_person_id": result.contacts[0]["person_id"] if result.contacts and not result.used_fallback else None,
        "matched_passage_id": result.links[0]["passage_id"] if result.links else None,
        "used_fallback": result.used_fallback,
    }])
    return result
