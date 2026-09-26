from datetime import date
from urllib.parse import parse_qs, unquote, urlparse

import pytest

from app.services.directory import Directory, working_hours
from tests.directory_seed import seed_directory

THURSDAY = date(2026, 10, 1)  # Tom is out of office until Oct 9; Grace works Mon-Thu
FRIDAY = date(2026, 10, 2)
LATER_MONDAY = date(2026, 10, 12)  # Tom's out-of-office date has passed


@pytest.fixture
def directory(repo):
    ids = seed_directory(repo)
    d = Directory.load(repo, "5e000000-0000-4000-8000-000000000001")
    d.ids = ids
    return d


def short(directory, who):
    return directory.short_ids[directory.ids[who]]


def test_topics_are_sorted_with_primary_descriptions(directory):
    assert [t for t, _ in directory.topics()] == ["bim", "office", "payroll"]
    assert dict(directory.topics())["payroll"].startswith("Paychecks")


def test_people_for_topic_orders_by_rank_and_marks_personal(directory):
    result = directory.people_for_topic("payroll")
    assert result["is_personal"] is True
    assert [p["name"] for p in result["people"]] == ["Tom Brennan", "Grace Liu"]
    assert result["people"][0]["person_id"] == short(directory, "tom")
    assert "email" not in result["people"][0]  # contact details stay server-side
    assert "error" in directory.people_for_topic("parking tickets")


@pytest.mark.parametrize("query", ["Riverside Library", "riverside", "RL-2301", "the library project"])
def test_project_role_matches_names_and_codes(directory, query):
    result = directory.project_role(query, "design_manager")
    assert result["project"] == "Riverside Library (RL-2301)"
    assert [p["name"] for p in result["people"]] == ["Rachel Adeyemi"]


def test_project_role_misses_are_explicit(directory):
    assert "No active project" in directory.project_role("Moon Base", "design_manager")["error"]
    assert "Unknown role" in directory.project_role("Riverside", "janitor")["error"]
    unassigned = directory.project_role("Harbor Point", "bim_lead")
    assert unassigned["people"] == [] and "No one is assigned" in unassigned["note"]


def test_search_people(directory):
    assert [p["name"] for p in directory.search_people("samir")["people"]] == ["Samir Haddad"]
    assert [p["name"] for p in directory.search_people("Rachel A")["people"]] == ["Rachel Adeyemi"]
    assert directory.search_people("Zed")["people"] == []


def test_working_hours_format():
    assert working_hours({"work_days": [1, 2, 3, 4, 5], "work_start": "08:30:00", "work_end": "17:00:00"}) == "Mon–Fri, 8:30 AM–5:00 PM"
    assert working_hours({"work_days": [1, 2, 3, 4], "work_start": "08:00", "work_end": "12:00"}) == "Mon–Thu, 8:00 AM–12:00 PM"
    assert working_hours({"work_days": [1, 3], "work_start": "09:00", "work_end": "13:15"}) == "Mon, Wed, 9:00 AM–1:15 PM"


def test_card_shows_backup_when_out_of_office(directory):
    card = directory.card(directory.ids["tom"], "Handles payroll", THURSDAY, "Payroll question", "I have a question about my pay.", "Alex Rivera")
    assert (card["name"], card["email"], card["is_in_today"], card["out_of_office_until"]) == (
        "Tom Brennan", "tom.brennan@studiomeridian.example", False, "2026-10-09")
    backup = card["backup"]
    assert (backup["name"], backup["is_in_today"], backup["backup"]) == ("Grace Liu", True, None)
    assert backup["reason"] == "Backup for Tom Brennan"

    url = urlparse(card["mailto"])
    assert url.scheme == "mailto" and url.path == "tom.brennan@studiomeridian.example"
    query = parse_qs(url.query)
    assert query["subject"] == ["Payroll question"]
    assert query["body"] == ["Hi Tom,\n\nI have a question about my pay.\n\nThanks,\nAlex Rivera"]


def test_card_availability_rules(directory):
    # Backup is shown on the backup's day off too, but it says they're out.
    friday = directory.card(directory.ids["tom"], "", FRIDAY)
    assert friday["backup"]["is_in_today"] is False
    # Once the out-of-office date passes, the person is back.
    assert directory.card(directory.ids["tom"], "", LATER_MONDAY)["is_in_today"] is True
    # People who are in don't get a backup.
    assert directory.card(directory.ids["samir"], "", THURSDAY)["backup"] is None
    # Weekends.
    assert directory.card(directory.ids["samir"], "", date(2026, 10, 3))["is_in_today"] is False


def test_mailto_without_draft(directory):
    card = directory.card(directory.ids["priya"], "", THURSDAY, sender="Alex Rivera")
    assert unquote(card["mailto"].split("body=")[1]) == "Hi Priya,\n\nThanks,\nAlex Rivera"
