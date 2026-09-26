"""The firm directory: lookups the assistant calls as tools, and contact cards.

Everything a contact card shows (name, title, email, hours, availability)
comes from directory rows, never from model output. Tools hand the model short
ids ("E3") that the server maps back to rows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time
from urllib.parse import quote
from zoneinfo import ZoneInfo

from app.db import Repo, Row

PROJECT_ROLES = [
    "principal_in_charge",
    "project_manager",
    "design_manager",
    "project_architect",
    "bim_lead",
    "designer",
    "intern",
]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STOPWORDS = {"the", "project", "for", "of", "and", "a", "an", "on"}


def _role_label(role: str) -> str:
    return role.replace("_", " ").capitalize()


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS}


@dataclass
class Directory:
    firm: Row
    people: dict[str, Row]  # uuid -> row
    responsibilities: list[Row]
    projects: list[Row]
    roles: list[Row]
    short_ids: dict[str, str] = field(default_factory=dict)  # uuid -> "E1"
    by_short: dict[str, str] = field(default_factory=dict)  # "E1" -> uuid

    def __post_init__(self):
        for n, person in enumerate(sorted(self.people.values(), key=lambda p: p["full_name"]), start=1):
            self.short_ids[person["id"]] = f"E{n}"
            self.by_short[f"E{n}"] = person["id"]

    @classmethod
    def load(cls, repo: Repo, firm_id: str) -> Directory:
        firm = repo.select_one("firms", {"id": firm_id}) or {"id": firm_id, "name": "your firm", "timezone": "UTC"}
        projects = repo.select("projects", {"firm_id": firm_id, "is_active": True}, order="name")
        return cls(
            firm=firm,
            people={p["id"]: p for p in repo.select("people", {"firm_id": firm_id})},
            responsibilities=repo.select("responsibilities", {"firm_id": firm_id}, order="rank"),
            projects=projects,
            roles=repo.select("project_roles", {"project_id": [p["id"] for p in projects]}),
        )

    # -- tool support -------------------------------------------------------

    def topics(self) -> list[tuple[str, str]]:
        """(topic, description of the primary contact's responsibility), sorted for a stable prompt."""
        seen: dict[str, str] = {}
        for r in sorted(self.responsibilities, key=lambda r: (r["topic"], r["rank"])):
            seen.setdefault(r["topic"], r["description"])
        return sorted(seen.items())

    def _summary(self, person_id: str) -> dict:
        p = self.people[person_id]
        return {"person_id": self.short_ids[person_id], "name": p["full_name"], "title": p["title"], "department": p["department"]}

    def people_for_topic(self, topic: str) -> dict:
        rows = [r for r in self.responsibilities if r["topic"] == topic and r["person_id"] in self.people]
        if not rows:
            return {"error": f"No one is listed for topic {topic!r}."}
        rows.sort(key=lambda r: r["rank"])
        return {
            "topic": topic,
            "is_personal": any(r["is_personal"] for r in rows),
            "people": [{**self._summary(r["person_id"]), "rank": r["rank"], "handles": r["description"]} for r in rows],
        }

    def match_projects(self, query: str) -> list[Row]:
        q = query.strip().lower()
        exact = [p for p in self.projects if p["code"].lower() == q or p["name"].lower() == q]
        if exact:
            return exact
        q_tokens = _tokens(query)
        return [
            p for p in self.projects
            if q and (q in p["name"].lower() or p["name"].lower() in q or (q_tokens and q_tokens <= _tokens(p["name"])))
        ]

    def project_role(self, project: str, role: str) -> dict:
        if role not in PROJECT_ROLES:
            return {"error": f"Unknown role {role!r}. Roles: {', '.join(PROJECT_ROLES)}."}
        matches = self.match_projects(project)
        if not matches:
            return {"error": f"No active project matches {project!r}.", "projects": [f"{p['name']} ({p['code']})" for p in self.projects]}
        if len(matches) > 1:
            return {"error": f"{project!r} matches several projects.", "projects": [f"{p['name']} ({p['code']})" for p in matches]}
        proj = matches[0]
        people = [r["person_id"] for r in self.roles if r["project_id"] == proj["id"] and r["role"] == role and r["person_id"] in self.people]
        result = {"project": f"{proj['name']} ({proj['code']})", "role": role}
        if not people:
            return {**result, "people": [], "note": "No one is assigned to this role on this project."}
        return {**result, "people": [self._summary(pid) for pid in people]}

    def search_people(self, name: str) -> dict:
        q = _tokens(name)
        if not q:
            return {"error": "Give a name to search for."}
        hits = [
            pid for pid, p in self.people.items()
            if all(any(t.startswith(qt) for t in _tokens(p["full_name"])) for qt in q)
        ]
        hits.sort(key=lambda pid: self.people[pid]["full_name"])
        return {"people": [self._summary(pid) for pid in hits[:5]]}

    # -- cards --------------------------------------------------------------

    def today(self) -> date:
        return datetime.now(ZoneInfo(self.firm.get("timezone") or "UTC")).date()

    def default_contact_id(self) -> str | None:
        pid = self.firm.get("default_contact_id")
        return pid if pid in self.people else None

    def card(
        self,
        person_id: str,
        reason: str,
        today: date,
        email_subject: str | None = None,
        email_body: str | None = None,
        sender: str = "",
        with_backup: bool = True,
    ) -> dict:
        p = self.people[person_id]
        out_until = _parse_date(p.get("out_of_office_until"))
        out_of_office = bool(p.get("is_out_of_office")) and (out_until is None or out_until >= today)
        in_today = not out_of_office and today.isoweekday() in (p.get("work_days") or [])

        card = {
            "person_id": person_id,
            "name": p["full_name"],
            "title": p["title"],
            "department": p["department"],
            "email": p["email"],
            "phone_ext": p.get("phone_ext"),
            "working_hours": working_hours(p),
            "is_in_today": in_today,
            "out_of_office_until": out_until.isoformat() if out_of_office and out_until else None,
            "reason": reason,
            "mailto": mailto(p, email_subject, email_body, sender),
            "backup": None,
        }
        backup_id = p.get("backup_person_id")
        if with_backup and not in_today and backup_id in self.people:
            card["backup"] = self.card(
                backup_id, f"Backup for {p['full_name']}", today, email_subject, email_body, sender, with_backup=False
            )
        return card


def _parse_date(value) -> date | None:
    if not value:
        return None
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _parse_time(value) -> time:
    return value if isinstance(value, time) else time.fromisoformat(str(value))


def _clock(t: time) -> str:
    return f"{t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"


def working_hours(person: Row) -> str:
    days = sorted(set(person.get("work_days") or []))
    if not days:
        return ""
    contiguous = days == list(range(days[0], days[-1] + 1))
    day_text = f"{DAY_NAMES[days[0] - 1]}–{DAY_NAMES[days[-1] - 1]}" if contiguous and len(days) > 2 else ", ".join(DAY_NAMES[d - 1] for d in days)
    return f"{day_text}, {_clock(_parse_time(person['work_start']))}–{_clock(_parse_time(person['work_end']))}"


def mailto(person: Row, subject: str | None, body: str | None, sender: str) -> str:
    first_name = person["full_name"].split()[0]
    text = f"Hi {first_name},\n\n{(body or '').strip()}\n\nThanks,\n{sender}".replace("\n\n\n\n", "\n\n")
    return f"mailto:{person['email']}?subject={quote((subject or '').strip())}&body={quote(text)}"
