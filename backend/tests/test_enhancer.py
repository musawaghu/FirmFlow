import json

import pytest

from app.services.enhancer import (
    DraftIssue,
    DraftModule,
    DraftPassage,
    EnhanceError,
    Enhancement,
    _user_prompt,
    enhance_manual,
    validate,
)
from app.services.parser import SourceSection
from tests.claude_mock import error_client, mock_client, sse

SECTIONS = [
    SourceSection(0, "6. TIMESHEETS", "Timesheets are due every Friday by 5:00 PM.\n\n3. Add a line.\n\n5. Enter your hours.", 9, 9),
    SourceSection(1, "6. TIMESHEETS › Reminder", "Reminder: all timesheets must be submitted by Monday at 12:00 noon.", 9, 9),
    SourceSection(2, "2. About the Studio", "The studio softball team plays Thursday evenings.", 2, 2),
]


def passage(section_id, content="Hand in your timesheet.", kind="text"):
    return DraftPassage(source_section_id=section_id, heading=None, kind=kind, content=content)


def issue(section_id, excerpt, type_="contradiction", related=None):
    return DraftIssue(type=type_, source_section_id=section_id, excerpt=excerpt, related_section_id=related, description="...")


def module(title, *passages):
    return DraftModule(title=title, summary="s", suggested_priority="day_1", passages=list(passages))


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

def test_valid_output_passes_through():
    result = validate(
        Enhancement(
            modules=[module("Timesheets", passage(0), passage(1))],
            issues=[issue(0, "due every Friday by 5:00 PM", related=1)],
        ),
        SECTIONS,
    )
    assert [m.title for m in result.modules] == ["Timesheets"]
    assert len(result.issues) == 1 and result.issues[0].related_section_id == 1
    assert result.unused_section_ids == [2]
    assert result.warnings == []


def test_passage_citing_unknown_section_is_dropped():
    result = validate(Enhancement(modules=[module("Timesheets", passage(0), passage(42))], issues=[]), SECTIONS)
    assert [p.source_section_id for p in result.modules[0].passages] == [0]
    assert "section 42" in result.warnings[0]


def test_module_with_no_valid_passages_is_dropped():
    result = validate(Enhancement(modules=[module("Ghost", passage(42), passage(0, content="  "))], issues=[]), SECTIONS)
    assert result.modules == []
    assert any("Dropped module 'Ghost'" in w for w in result.warnings)


def test_issue_with_invented_excerpt_is_dropped():
    result = validate(
        Enhancement(modules=[], issues=[issue(0, "Timesheets are due Thursday")]),
        SECTIONS,
    )
    assert result.issues == []
    assert "excerpt is not in section 0" in result.warnings[0]


def test_issue_excerpt_matching_is_loose_about_formatting():
    # Curly quotes, case, extra whitespace, and list markers don't matter.
    sections = [SourceSection(0, None, '- Check "Detach from Central" at the bottom.', 1, 1)]
    result = validate(
        Enhancement(modules=[], issues=[issue(0, "check “detach  from Central”", type_="missing_step")]),
        sections,
    )
    assert len(result.issues) == 1


def test_issue_citing_unknown_section_is_dropped_and_bad_related_id_cleared():
    result = validate(
        Enhancement(
            modules=[],
            issues=[issue(9, "anything"), issue(1, "Monday at 12:00 noon", related=77)],
        ),
        SECTIONS,
    )
    assert len(result.issues) == 1
    assert result.issues[0].related_section_id is None


def test_duplicate_issues_are_collapsed():
    dup = issue(0, "Friday by 5:00 PM")
    result = validate(Enhancement(modules=[], issues=[dup, dup]), SECTIONS)
    assert len(result.issues) == 1


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def test_prompt_lists_sections_with_ids_and_pages():
    prompt = _user_prompt(SECTIONS, None)
    assert '<section id="1" pages="9">' in prompt
    assert "<heading>6. TIMESHEETS › Reminder</heading>" in prompt
    assert "admin wants these modules" not in prompt


def test_prompt_includes_module_topics():
    prompt = _user_prompt(SECTIONS, ["Timesheets", "Payroll & Benefits: payroll, PTO"])
    assert "- Timesheets\n- Payroll & Benefits: payroll, PTO" in prompt
    assert "only the part before the colon as the module title" in prompt


# ---------------------------------------------------------------------------
# enhance_manual() through the real SDK, with the HTTP layer mocked
# ---------------------------------------------------------------------------

GOOD_OUTPUT = {
    "modules": [{
        "title": "Timesheets",
        "summary": "When and how to submit your timesheet.",
        "suggested_priority": "day_1",
        "passages": [{"source_section_id": 0, "heading": "Deadline", "kind": "text",
                      "content": "Your timesheet is due every Friday by 5:00 PM."}],
    }],
    "issues": [{"type": "contradiction", "source_section_id": 0, "excerpt": "every Friday by 5:00 PM",
                "related_section_id": 1, "description": "Section 1 says Monday at noon."}],
}


def test_enhance_manual_request_and_result():
    requests = []
    client = mock_client(sse(payload=GOOD_OUTPUT), requests)

    result = enhance_manual(SECTIONS, client=client, model="claude-opus-5", module_topics=["Timesheets"])

    body = json.loads(requests[0].content)
    assert body["model"] == "claude-opus-5"
    assert body["stream"] is True
    assert body["thinking"] == {"type": "adaptive"}
    assert body["output_config"]["effort"] == "high"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in requests[0].headers["anthropic-beta"]
    assert "never invents anything" in body["system"]

    assert [m.title for m in result.modules] == ["Timesheets"]
    assert result.issues[0].related_section_id == 1
    assert result.unused_section_ids == [1, 2]
    assert (result.model, result.input_tokens, result.output_tokens) == ("claude-opus-5", 1200, 850)


@pytest.mark.parametrize(
    ("stop_reason", "message"),
    [("refusal", "declined"), ("max_tokens", "too long")],
)
def test_enhance_manual_bad_stop_reasons(stop_reason, message):
    client = mock_client(sse(stop_reason=stop_reason, payload=GOOD_OUTPUT), [])
    with pytest.raises(EnhanceError, match=message):
        enhance_manual(SECTIONS, client=client, model="claude-opus-5")


def test_enhance_manual_api_error():
    with pytest.raises(EnhanceError, match="400"):
        enhance_manual(SECTIONS, client=error_client(400), model="claude-opus-5")


def test_enhance_manual_rejects_empty_manual():
    with pytest.raises(EnhanceError, match="no sections"):
        enhance_manual([], client=mock_client("", []))


def test_unreadable_output_is_an_enhance_error():
    # A refusal can stop mid-output; parsing the partial text must not crash the caller.
    client = mock_client(sse(stop_reason="refusal", payload={"modules": "partial"}), [])
    with pytest.raises(EnhanceError, match="could not be read"):
        enhance_manual(SECTIONS, client=client, model="claude-opus-5")
