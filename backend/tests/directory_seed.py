"""A slice of supabase/seed.sql for directory and assistant tests."""

from tests.conftest import FIRM_A


def person(name, title, dept, days="12345", start="08:30:00", end="17:00:00", ooo=False, until=None):
    first, last = name.lower().split()
    return {
        "firm_id": FIRM_A, "full_name": name, "title": title, "department": dept,
        "email": f"{first}.{last}@studiomeridian.example", "phone_ext": "100",
        "work_days": [int(d) for d in days], "work_start": start, "work_end": end,
        "is_out_of_office": ooo, "out_of_office_until": until, "backup_person_id": None,
    }


def seed_directory(repo) -> dict:
    rows = repo.insert("people", [
        person("Priya Raman", "Office Manager", "Operations", start="08:00:00", end="16:30:00"),
        person("Tom Brennan", "Payroll & Accounting Manager", "Finance", ooo=True, until="2026-10-09"),
        person("Grace Liu", "Accounting Specialist", "Finance", days="1234", start="08:00:00", end="16:30:00"),
        person("Samir Haddad", "BIM Manager", "Technology"),
        person("Keiko Tanaka", "BIM Coordinator", "Technology"),
        person("Rachel Adeyemi", "Design Manager", "Studio", start="09:00:00", end="17:30:00"),
        person("Omar Siddiqui", "Design Manager", "Studio", start="09:00:00", end="17:30:00"),
    ])
    ids = {r["full_name"].split()[0].lower(): r["id"] for r in rows}
    for who, backup in (("tom", "grace"), ("grace", "tom"), ("samir", "keiko"), ("rachel", "omar")):
        repo.update("people", ids[who], {"backup_person_id": ids[backup]})

    repo.insert("firms", [{"id": FIRM_A, "name": "Studio Meridian Architects", "timezone": "America/Los_Angeles",
                           "default_contact_id": ids["priya"]}])
    repo.insert("responsibilities", [
        {"firm_id": FIRM_A, "person_id": ids["tom"], "topic": "payroll", "rank": 1, "is_personal": True,
         "description": "Paychecks, pay stubs, direct deposit, tax withholding, and W-2s.", "keywords": []},
        {"firm_id": FIRM_A, "person_id": ids["grace"], "topic": "payroll", "rank": 2, "is_personal": True,
         "description": "Backup for payroll questions.", "keywords": []},
        {"firm_id": FIRM_A, "person_id": ids["samir"], "topic": "bim", "rank": 1, "is_personal": False,
         "description": "BIM standards, Revit templates, worksharing, and central models.", "keywords": []},
        {"firm_id": FIRM_A, "person_id": ids["keiko"], "topic": "bim", "rank": 2, "is_personal": False,
         "description": "Backup for BIM questions.", "keywords": []},
        {"firm_id": FIRM_A, "person_id": ids["priya"], "topic": "office", "rank": 1, "is_personal": False,
         "description": "Building access, key cards, parking, desks, and supplies.", "keywords": []},
    ])
    riverside, harbor = repo.insert("projects", [
        {"firm_id": FIRM_A, "code": "RL-2301", "name": "Riverside Library", "client": "City", "phase": "CD", "is_active": True},
        {"firm_id": FIRM_A, "code": "HP-2204", "name": "Harbor Point Mixed-Use", "client": "Harborline", "phase": "DD", "is_active": True},
    ])
    repo.insert("project_roles", [
        {"project_id": riverside["id"], "person_id": ids["rachel"], "role": "design_manager"},
        {"project_id": riverside["id"], "person_id": ids["keiko"], "role": "bim_lead"},
        {"project_id": harbor["id"], "person_id": ids["omar"], "role": "design_manager"},
    ])
    return ids
