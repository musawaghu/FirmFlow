"""Final onboarding check: question bank review (admin) and attempts (employees)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.auth import Profile, get_current_profile, require_admin
from app.db import Repo, Row, get_repo
from app.ratelimit import rate_limit
from app.schemas import AnswerOut, AttemptOut, GenerateOut, QuestionOut
from app.services.content import firm_content
from app.services.parser import SourceSection
from app.services.progress import final_check_unlocked, load_progress, required_progress
from app.services.quiz import (
    MAX_ANSWER_CHARS,
    CriticalPassage,
    DraftQuestion,
    QuizError,
    generate_questions,
    grade_scenario,
    question_problem,
    select_questions,
)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class QuestionUpdate(BaseModel):
    prompt: str | None = None
    choices: list[str] | None = None
    correct_choice: int | None = None
    rubric: str | None = None
    explanation: str | None = None
    status: Literal["draft", "approved", "rejected"] | None = None


class AnswerIn(BaseModel):
    question_id: str
    selected_choice: int | None = None  # multiple choice
    answer_text: str | None = None  # scenario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def section_links(repo: Repo, passage_ids: list[str]) -> dict[str, dict]:
    """passage id -> the module section to link to."""
    passages = repo.select("module_passages", {"id": list(set(passage_ids))})
    modules = {m["id"]: m for m in repo.select("modules", {"id": list({p["module_id"] for p in passages})})}
    return {
        p["id"]: {
            "module_id": p["module_id"],
            "module_title": modules[p["module_id"]]["title"],
            "passage_id": p["id"],
            "passage_heading": p["heading"],
        }
        for p in passages
        if p["module_id"] in modules
    }


def _eligible_passages(repo: Repo, firm_id: str) -> tuple[dict[str, Row], dict[str, Row]]:
    """Critical passages in the firm's approved firm and baseline modules, and those modules, keyed by id."""
    content = firm_content(repo, firm_id)
    return {p["id"]: p for p in content.critical_passages()}, {m["id"]: m for m in content.modules}


def _question_out(question: Row, links: dict[str, dict]) -> dict:
    return {**question, "link": links.get(question["passage_id"])}


def _to_source(s: Row) -> SourceSection:
    return SourceSection(s["ordinal"], s["heading"], s["content"], s["page_start"], s["page_end"])


def _source_for(repo: Repo, passage_id: str) -> SourceSection:
    passage = repo.select_one("module_passages", {"id": passage_id})
    return _to_source(repo.select_one("source_sections", {"id": passage["source_section_id"]}))


# ---------------------------------------------------------------------------
# Admin: question bank
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=GenerateOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("quiz_generate"))])
def generate(profile: Profile = Depends(require_admin), repo: Repo = Depends(get_repo)):
    """Draft questions from the critical passages in approved modules.

    Replaces earlier drafts. Refused once any question is approved; reject the
    approved questions first to start over.
    """
    if repo.select("quiz_questions", {"firm_id": profile.firm_id, "status": "approved"}):
        raise HTTPException(status.HTTP_409_CONFLICT, "The question bank is already approved. Reject its questions to generate a new one.")

    passages, modules = _eligible_passages(repo, profile.firm_id)
    if not passages:
        raise HTTPException(status.HTTP_409_CONFLICT, "Mark passages in approved modules as critical first")

    section_ids = list({p["source_section_id"] for p in passages.values()})
    sections = {s["id"]: s for s in repo.select("source_sections", {"id": section_ids})}
    critical = [
        CriticalPassage(
            passage_id=p["id"],
            module_title=modules[p["module_id"]]["title"],
            heading=p["heading"],
            content=p["content"],
            source=_to_source(sections[p["source_section_id"]]),
        )
        for p in passages.values()
    ]
    try:
        generated = generate_questions(critical)
    except QuizError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Could not generate questions: {exc}") from exc

    repo.delete("quiz_questions", {"firm_id": profile.firm_id, "status": "draft"})
    rows = repo.insert("quiz_questions", [
        {
            "id": str(uuid.uuid4()),
            "firm_id": profile.firm_id,
            "passage_id": passage_id,
            "type": q.type,
            "prompt": q.prompt,
            "choices": q.choices,
            "correct_choice": q.correct_choice,
            "rubric": q.rubric,
            "explanation": q.explanation,
            "status": "draft",
        }
        for passage_id, q in generated.questions
    ])
    links = section_links(repo, [r["passage_id"] for r in rows])
    return {"questions": [_question_out(r, links) for r in rows], "warnings": generated.warnings}


@router.get("/questions", response_model=list[QuestionOut])
def list_questions(
    question_status: Literal["draft", "approved", "rejected"] | None = Query(default=None, alias="status"),
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    filters = {"firm_id": profile.firm_id}
    if question_status:
        filters["status"] = question_status
    questions = repo.select("quiz_questions", filters, order="created_at")
    links = section_links(repo, [q["passage_id"] for q in questions])
    return [_question_out(q, links) for q in questions]


@router.patch("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: str,
    body: QuestionUpdate,
    profile: Profile = Depends(require_admin),
    repo: Repo = Depends(get_repo),
):
    """Edit, approve, or reject a question. Approved questions must go back to draft to be edited."""
    question = repo.select_one("quiz_questions", {"id": question_id, "firm_id": profile.firm_id}) if _valid_uuid(question_id) else None
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    edits = {f: getattr(body, f) for f in ("prompt", "choices", "correct_choice", "rubric", "explanation") if f in body.model_fields_set}
    if edits and question["status"] == "approved" and body.status != "draft":
        raise HTTPException(status.HTTP_409_CONFLICT, "Move the question back to draft before editing it")

    merged = DraftQuestion(**{
        **{k: question[k] for k in ("type", "prompt", "choices", "correct_choice", "rubric", "explanation")},
        "passage_id": question["passage_id"],
        **edits,
    })
    if problem := question_problem(merged):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Invalid question: {problem}")
    if merged.type == "multiple_choice":
        edits["choices"] = [c.strip() for c in merged.choices]

    if body.status == "approved" and question["status"] != "approved":
        passages, _ = _eligible_passages(repo, profile.firm_id)
        if question["passage_id"] not in passages:
            raise HTTPException(status.HTTP_409_CONFLICT, "This question's passage is no longer critical in an approved module")

    changes = {**edits, **({"status": body.status} if body.status else {})}
    if changes:
        question = repo.update("quiz_questions", question_id, changes)
    return _question_out(question, section_links(repo, [question["passage_id"]]))


# ---------------------------------------------------------------------------
# Employees: attempts
# ---------------------------------------------------------------------------

def _attempt_view(repo: Repo, attempt: Row) -> dict:
    ids = attempt["question_ids"]
    questions = {q["id"]: q for q in repo.select("quiz_questions", {"id": ids})}
    answers = repo.select("quiz_answers", {"attempt_id": attempt["id"]})
    links = section_links(repo, [q["passage_id"] for q in questions.values()])

    out = []
    for qid in ids:
        q = questions.get(qid)
        if q is None:
            continue
        mine = [a for a in answers if a["question_id"] == qid]
        state = "correct" if any(a["is_correct"] for a in mine) else "missed" if mine else "unanswered"
        out.append({
            "id": qid,
            "type": q["type"],
            "prompt": q["prompt"],
            "choices": q["choices"],
            "state": state,
            "tries": len(mine),
            "link": links.get(q["passage_id"]) if state == "missed" else None,
        })
    return {**attempt, "questions": out}


def _get_attempt(repo: Repo, profile: Profile, attempt_id: str) -> Row:
    attempt = repo.select_one("quiz_attempts", {"id": attempt_id, "profile_id": profile.id}) if _valid_uuid(attempt_id) else None
    if attempt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attempt not found")
    return attempt


@router.post("/attempts", response_model=AttemptOut, status_code=status.HTTP_201_CREATED)
def start_attempt(response: Response, profile: Profile = Depends(get_current_profile), repo: Repo = Depends(get_repo)):
    """Start the final check, or resume the one in progress. Unlocks after all required modules."""
    modules, progress = load_progress(repo, profile.firm_id, profile.id)
    if not final_check_unlocked(*required_progress(modules, progress)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Finish all required modules to unlock the final check")

    current = repo.select_one("quiz_attempts", {"profile_id": profile.id, "status": "in_progress"})
    if current is not None:
        response.status_code = status.HTTP_200_OK
        return _attempt_view(repo, current)

    passages, _ = _eligible_passages(repo, profile.firm_id)
    bank = [q for q in repo.select("quiz_questions", {"firm_id": profile.firm_id, "status": "approved"}) if q["passage_id"] in passages]
    if not bank:
        raise HTTPException(status.HTTP_409_CONFLICT, "The final check isn't ready yet. Ask your admin.")

    attempt = repo.insert("quiz_attempts", [{
        "firm_id": profile.firm_id,
        "profile_id": profile.id,
        "question_ids": select_questions(bank),
        "status": "in_progress",
        "started_at": _now(),
    }])[0]
    return _attempt_view(repo, attempt)


@router.get("/attempts/current", response_model=AttemptOut)
def current_attempt(profile: Profile = Depends(get_current_profile), repo: Repo = Depends(get_repo)):
    """The attempt in progress, or else the most recent one."""
    attempts = repo.select("quiz_attempts", {"profile_id": profile.id}, order="started_at")
    if not attempts:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No attempts yet")
    in_progress = [a for a in attempts if a["status"] == "in_progress"]
    return _attempt_view(repo, (in_progress or attempts)[-1])


@router.post("/attempts/{attempt_id}/answers", response_model=AnswerOut, dependencies=[Depends(rate_limit("quiz_answer"))])
def answer(attempt_id: str, body: AnswerIn, profile: Profile = Depends(get_current_profile), repo: Repo = Depends(get_repo)):
    """Answer one question and get instant feedback. Missed questions can be answered again."""
    attempt = _get_attempt(repo, profile, attempt_id)
    if attempt["status"] != "in_progress":
        raise HTTPException(status.HTTP_409_CONFLICT, "This attempt is already complete")
    if body.question_id not in attempt["question_ids"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That question isn't part of this attempt")

    question = repo.select_one("quiz_questions", {"id": body.question_id})
    previous = repo.select("quiz_answers", {"attempt_id": attempt_id, "question_id": body.question_id})
    if any(a["is_correct"] for a in previous):
        raise HTTPException(status.HTTP_409_CONFLICT, "You already answered this question correctly")

    link = section_links(repo, [question["passage_id"]]).get(question["passage_id"])
    review = f"Review “{link['passage_heading'] or link['module_title']}” in {link['module_title']}" if link else "Review the module"

    if question["type"] == "multiple_choice":
        if body.selected_choice is None or not 0 <= body.selected_choice < len(question["choices"]):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choose one of the options")
        is_correct = body.selected_choice == question["correct_choice"]
        # Don't reveal the answer on a miss; the retry should follow a review.
        feedback = question["explanation"] if is_correct else f"Not quite. {review} and try again."
    else:
        text = (body.answer_text or "").strip()
        if not text:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Write an answer")
        if len(text) > MAX_ANSWER_CHARS:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Keep your answer under {MAX_ANSWER_CHARS} characters")
        try:
            grade = grade_scenario(
                prompt=question["prompt"],
                rubric=question["rubric"],
                answer=text,
                source=_source_for(repo, question["passage_id"]),
            )
        except QuizError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Grading is unavailable right now. Try again in a moment.") from exc
        is_correct = grade.is_correct
        feedback = grade.feedback if is_correct else f"{grade.feedback} {review}."

    try_number = len(previous) + 1
    repo.insert("quiz_answers", [{
        "attempt_id": attempt_id,
        "question_id": body.question_id,
        "try_number": try_number,
        "selected_choice": body.selected_choice if question["type"] == "multiple_choice" else None,
        "answer_text": body.answer_text.strip() if question["type"] == "scenario" else None,
        "is_correct": is_correct,
        "feedback": feedback,
    }])

    # Complete once every question has a correct answer; score counts first tries.
    answers = repo.select("quiz_answers", {"attempt_id": attempt_id})
    ids = attempt["question_ids"]
    if all(any(a["is_correct"] for a in answers if a["question_id"] == qid) for qid in ids):
        first_try = sum(1 for a in answers if a["try_number"] == 1 and a["is_correct"])
        attempt = repo.update("quiz_attempts", attempt_id, {
            "status": "completed",
            "completed_at": _now(),
            "score": round(first_try / len(ids) * 100, 2),
        })

    return {
        "question_id": body.question_id,
        "is_correct": is_correct,
        "feedback": feedback,
        "try_number": try_number,
        "link": None if is_correct else link,
        "attempt": _attempt_view(repo, attempt),
    }
