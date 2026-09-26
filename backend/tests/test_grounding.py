import json
from pathlib import Path

import pytest

from app.services import grounding
from app.services.enhancer import DraftModule, DraftPassage, EnhancementResult
from app.services.grounding import (
    GroundingError,
    PassageInput,
    check_enhancement,
    check_passages,
    find_omissions,
    rule_spans,
)
from app.services.parser import SourceSection, parse_manual
from tests.claude_mock import error_client, mock_client, sse

SAMPLES = Path(__file__).resolve().parents[2] / "samples"

TIMESHEETS = SourceSection(
    0,
    "6. TIMESHEETS",
    "Timesheets are due every Friday by 5:00 PM for the current week.\n\n"
    "3. For each project, add a line (for example, RL-2301 / CD).\n\n"
    "5. Enter your hours. Round to the nearest quarter hour.\n\n"
    "Questions go to Grace Liu (grace.liu@studiomeridian.example), ext. 121.",
    9,
    9,
)
PTO = SourceSection(
    1,
    "8. PTO › Requesting time off",
    "PTO requests must be submitted at least two weeks in advance. "
    "See https://hr.studiomeridian.example/portal and \\\\SM-FS02\\Projects\\Forms\\pto.pdf.",
    11,
    11,
)


def p(content, source=TIMESHEETS, key="k", heading=None):
    return PassageInput(key=key, heading=heading, content=content, source=source)


def spans(passage):
    return [s.text for s in rule_spans(passage)]


# ---------------------------------------------------------------------------
# Rule check: passage -> source
# ---------------------------------------------------------------------------

def test_faithful_rewrite_passes():
    assert spans(p("Submit your timesheet every Friday by 5 PM. Use project RL-2301 and phase CD.")) == []


def test_changed_time_is_flagged():
    assert spans(p("Submit your timesheet every Friday by 6:00 PM.")) == ["6:00"]


def test_invented_number_is_flagged_once():
    assert spans(p("Late timesheets cost 10 points. Really, 10 points.")) == ["10"]


def test_number_words_and_digits_match():
    assert spans(p("Request PTO at least 2 weeks ahead.", source=PTO)) == []
    assert spans(p("Request PTO at least 3 weeks ahead.", source=PTO)) == ["3"]


def test_list_markers_are_not_facts():
    content = "1. Open your timesheet.\n2. Add a line for each project.\n3. Enter your hours."
    assert spans(p(content)) == []


def test_changed_or_invented_links_are_flagged():
    assert spans(p("Use https://hr.studiomeridian.example/portal.", source=PTO)) == []
    assert spans(p("Use https://hr.studiomeridian.example/pto-form.", source=PTO)) == ["https://hr.studiomeridian.example/pto-form"]
    assert spans(p("Email grace.liu@studiomeridian.example.")) == []
    assert spans(p("Email payroll@studiomeridian.example.")) == ["payroll@studiomeridian.example"]
    assert spans(p("Save it to \\\\SM-FS02\\Projects\\Forms\\pto.pdf.", source=PTO)) == []
    assert spans(p("Save it to \\\\SM-FS01\\Forms\\pto.pdf.", source=PTO)) == ["\\\\SM-FS01\\Forms\\pto.pdf"]


def test_heading_is_checked_too():
    assert spans(p("Submit on Friday.", heading="Due by 4 PM")) == ["4"]


def test_numbers_in_source_heading_count_as_support():
    source = SourceSection(3, "4. BIM › 4.2 Making a test copy", "Use Detach from Central.", 5, 5)
    assert spans(p("Use Detach from Central.", source=source, heading="4.2 Test copies")) == []


def test_unchanged_sample_manual_is_clean():
    # Every parsed section checked against itself: no false positives.
    for file_type in ("pdf", "docx"):
        sections = parse_manual((SAMPLES / f"studio_meridian_manual.{file_type}").read_bytes(), file_type).sections
        result = check_passages([p(s.content, source=s, key=str(s.ordinal), heading=s.heading) for s in sections], use_model=False)
        assert result.flagged == []
        assert result.omissions == []


# ---------------------------------------------------------------------------
# Rule check: source -> passages (omissions)
# ---------------------------------------------------------------------------

def test_dropped_facts_are_reported():
    omissions = find_omissions([p("Submit your timesheet every Friday by 5:00 PM.")])
    assert [o.text for o in omissions] == ["grace.liu@studiomeridian.example", "2301", "121"]
    assert {o.section_id for o in omissions} == {0}


def test_facts_split_across_passages_are_not_omissions():
    omissions = find_omissions([
        p("Due every Friday by 5:00 PM. Use RL-2301 / CD.", key="a"),
        p("Ask Grace Liu (grace.liu@studiomeridian.example, ext. 121).", key="b"),
    ])
    assert omissions == []


# ---------------------------------------------------------------------------
# Model check (real SDK, mocked HTTP)
# ---------------------------------------------------------------------------

def model_output(*spans):
    return {"unsupported": [{"passage_id": pid, "text": text, "reason": "not in source"} for pid, text in spans]}


def test_model_spans_are_located_and_merged_with_rules():
    passages = [
        p("You must submit your timesheet every Friday by 6:00 PM.", key="m0.p0"),
        p("Round to the nearest quarter hour.", key="m0.p1"),
    ]
    requests = []
    client = mock_client(sse(model_output(
        ("P1", "You MUST submit"),     # different case: located with the passage's own text
        ("P1", "6:00"),                # already found by the rule check: not duplicated
        ("P2", "a quote that isn't there"),
        ("P9", "unknown passage"),
    )), requests)

    result = check_passages(passages, client=client, model="claude-opus-5")

    first = result.passages["m0.p0"]
    assert [(s.text, s.check, s.located) for s in first.unsupported_spans] == [
        ("6:00", "rule", True),
        ("You must submit", "model", True),
    ]
    second = result.passages["m0.p1"]
    assert not second.grounding_ok
    assert [(s.text, s.located) for s in second.unsupported_spans] == [("a quote that isn't there", False)]
    assert "unknown passage 'P9'" in result.warnings[0]
    assert (result.input_tokens, result.output_tokens) == (1200, 850)

    body = json.loads(requests[0].content)
    assert body["output_config"]["effort"] == "high"
    assert '<passage id="P2" source="0">' in body["messages"][0]["content"]
    assert body["messages"][0]["content"].count('<section id="0">') == 1  # sources deduplicated


def test_clean_model_result_leaves_passages_ok():
    result = check_passages([p("Round to the nearest quarter hour.")], client=mock_client(sse(model_output())))
    assert result.flagged == []


def test_passages_are_batched(monkeypatch):
    monkeypatch.setattr(grounding, "BATCH_SIZE", 2)
    requests = []
    client = mock_client(sse(model_output()), requests)
    result = check_passages([p("Round to the nearest quarter hour.", key=str(i)) for i in range(5)], client=client)
    assert len(requests) == 3
    assert result.input_tokens == 3 * 1200


def test_use_model_false_makes_no_request():
    requests = []
    check_passages([p("Friday by 6:00 PM.")], use_model=False, client=mock_client(sse(model_output()), requests))
    assert requests == []


def test_model_failure_raises_grounding_error():
    with pytest.raises(GroundingError, match="400"):
        check_passages([p("Friday.")], client=error_client(400))


def test_check_enhancement_keys_passages_by_position():
    enhancement = EnhancementResult(
        modules=[DraftModule(title="Time", summary="s", suggested_priority="day_1", passages=[
            DraftPassage(source_section_id=0, heading=None, kind="text", content="Due Friday by 5 PM."),
            DraftPassage(source_section_id=1, heading=None, kind="text", content="Ask 4 weeks ahead."),
        ])],
        issues=[],
        unused_section_ids=[],
    )
    result = check_enhancement(enhancement, [TIMESHEETS, PTO], use_model=False)
    assert result.passages["0.0"].grounding_ok
    assert [s.text for s in result.passages["0.1"].unsupported_spans] == ["4"]
