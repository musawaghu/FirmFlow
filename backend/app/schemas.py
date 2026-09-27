"""Response models shared by the routers. Rows come straight from Supabase; extra columns are ignored."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class _Out(BaseModel):
    model_config = ConfigDict(extra="ignore")


class MeOut(BaseModel):
    id: str
    full_name: str
    email: str
    role: str  # admin | employee
    firm_id: str
    firm_name: str | None


class ManualOut(_Out):
    id: str
    title: str
    file_type: str
    page_count: int | None
    status: str
    error: str | None
    processing_notes: dict[str, Any]
    created_at: str


class SectionOut(_Out):
    id: str
    ordinal: int
    heading: str | None
    content: str
    page_start: int | None
    page_end: int | None


class PassageOut(_Out):
    id: str
    source_section_id: str
    ordinal: int
    heading: str | None
    content: str
    kind: str
    is_critical: bool
    grounding_ok: bool | None
    unsupported_spans: list[dict[str, Any]]


class ModuleOut(_Out):
    id: str
    title: str
    summary: str | None
    ordinal: int
    priority: str
    is_required: bool
    status: str
    passages: list[PassageOut]


class PassageRef(BaseModel):
    passage_id: str
    heading: str | None
    module_id: str
    module_title: str


class OverrideOut(_Out):
    """A firm passage that replaces a baseline passage once the admin confirms it."""
    id: str
    status: str  # proposed | confirmed | dismissed
    difference: str
    firm_excerpt: str
    baseline_excerpt: str
    firm_passage: PassageRef
    baseline_passage: PassageRef


class ReviewOut(BaseModel):
    manual: ManualOut
    sections: list[SectionOut]
    modules: list[ModuleOut]
    overrides: list[OverrideOut] = []


# ---------------------------------------------------------------------------
# AEC baseline (admin): shared modules and this firm's settings for them
# ---------------------------------------------------------------------------

class BaselinePassageOut(_Out):
    id: str
    ordinal: int
    heading: str | None
    content: str
    kind: str
    is_critical: bool  # for this firm
    overridden_by: str | None = None  # confirmed override id, if the firm's rule replaces this passage


class BaselineModuleOut(_Out):
    id: str
    title: str
    summary: str | None
    priority: str  # this firm's setting, or the baseline default
    is_required: bool
    ordinal: int
    is_hidden: bool
    passages: list[BaselinePassageOut]


class IssueOut(_Out):
    id: str
    type: str
    description: str
    excerpt: str | None
    status: str
    module_id: str | None
    source_section_id: str | None
    related_section_id: str | None
    section_heading: str | None = None
    pages: str | None = None


class PassageEditOut(PassageOut):
    grounding_error: str | None = None  # set when the re-check couldn't run; grounding_ok is then null


# ---------------------------------------------------------------------------
# Employee views: approved content only, no grounding details
# ---------------------------------------------------------------------------

class EmployeePassageOut(_Out):
    id: str
    ordinal: int
    heading: str | None
    content: str
    kind: str
    # Baseline passage replaced by the firm's own rule: the content above is the firm's,
    # firm_note says so, and firm_passage_id links to it in the firm's module.
    overridden_by_firm: bool = False
    firm_note: str | None = None
    firm_passage_id: str | None = None


class ProgressOut(_Out):
    module_id: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None


class EmployeeModuleOut(_Out):
    id: str
    layer: str = "firm"  # firm | baseline (shared AEC content)
    title: str
    summary: str | None
    priority: str
    is_required: bool
    progress: str  # not_started | in_progress | completed
    passages: list[EmployeePassageOut]


class ModuleListOut(BaseModel):
    full_name: str
    required_modules: int
    completed_required: int
    final_check_unlocked: bool
    modules: list[EmployeeModuleOut]


# ---------------------------------------------------------------------------
# Final onboarding check
# ---------------------------------------------------------------------------

class SectionLink(BaseModel):
    """Where to review: the module section a question was written from."""
    module_id: str
    module_title: str
    passage_id: str
    passage_heading: str | None


class QuestionOut(_Out):
    """Admin view of a question, including the answer key."""
    id: str
    passage_id: str
    type: str
    prompt: str
    choices: list[str] | None
    correct_choice: int | None
    rubric: str | None
    explanation: str
    status: str
    link: SectionLink | None = None


class GenerateOut(BaseModel):
    questions: list[QuestionOut]
    warnings: list[str]


class AttemptQuestionOut(BaseModel):
    """Employee view of a question: no answer key."""
    id: str
    type: str
    prompt: str
    choices: list[str] | None
    state: str  # unanswered | missed | correct
    tries: int
    link: SectionLink | None = None  # shown once the question has been missed


class AttemptOut(_Out):
    id: str
    status: str
    score: float | None
    started_at: str
    completed_at: str | None
    questions: list[AttemptQuestionOut]


class AnswerOut(BaseModel):
    question_id: str
    is_correct: bool
    feedback: str
    try_number: int
    link: SectionLink | None  # the module section to review after a miss
    attempt: AttemptOut


class FailedQuestionOut(BaseModel):
    question_id: str
    prompt: str
    type: str
    status: str
    first_tries: int
    first_try_misses: int
    miss_rate: float
    link: SectionLink | None


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------

class ContactCard(BaseModel):
    """Built from a directory row; nothing here comes from model output."""
    person_id: str
    name: str
    title: str
    department: str
    email: str
    phone_ext: str | None
    working_hours: str
    is_in_today: bool
    out_of_office_until: str | None
    reason: str
    mailto: str  # pre-drafted email the employee can edit before sending
    backup: "ContactCard | None" = None  # shown when the person isn't in today


class ChatOut(BaseModel):
    intent: str
    answer: str
    links: list[SectionLink]
    contacts: list[ContactCard]
    used_fallback: bool


class UnansweredOut(_Out):
    id: str
    question: str
    answer: str | None
    created_at: str


# ---------------------------------------------------------------------------
# Admin progress
# ---------------------------------------------------------------------------

class ModuleStatusOut(BaseModel):
    module_id: str
    layer: str = "firm"  # firm | baseline
    title: str
    priority: str
    is_required: bool
    status: str  # not_started | in_progress | completed


class FinalCheckOut(BaseModel):
    status: str  # locked | not_started | in_progress | completed
    score: float | None  # percent correct on first tries, from the latest completed attempt
    attempts: int
    completed_at: str | None


class EmployeeProgressOut(BaseModel):
    profile_id: str
    full_name: str
    email: str
    start_date: str | None
    stage: str  # not_started | in_progress | modules_done | complete
    required_modules: int
    completed_required: int
    modules: list[ModuleStatusOut]
    final_check: FinalCheckOut
    last_activity_at: str | None


class AdminProgressOut(BaseModel):
    required_modules: int
    employees: list[EmployeeProgressOut]
