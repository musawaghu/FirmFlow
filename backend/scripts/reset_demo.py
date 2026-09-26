"""Reset an employee's onboarding so the demo can be run again.

Deletes their module progress, final check attempts (and answers), and
assistant chat logs. Modules, quiz questions, and the directory are kept.
From backend/:
    .venv/bin/python -m scripts.reset_demo                                   # Alex (demo intern)
    .venv/bin/python -m scripts.reset_demo jamie.cho@studiomeridian.example
"""

import sys

from app.db import get_repo

DEFAULT_EMAIL = "alex.rivera@studiomeridian.example"
TABLES = ["module_progress", "quiz_attempts", "chat_logs"]  # quiz_answers cascade from quiz_attempts


def main() -> None:
    email = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
    repo = get_repo()
    profile = repo.select_one("profiles", {"email": email})
    if profile is None:
        print(f"No profile for {email}", file=sys.stderr)
        sys.exit(1)
    if profile["role"] != "employee":
        print(f"{email} is an {profile['role']}, not an employee; refusing to reset", file=sys.stderr)
        sys.exit(1)

    for table in TABLES:
        count = len(repo.select(table, {"profile_id": profile["id"]}))
        repo.delete(table, {"profile_id": profile["id"]})
        print(f"{table}: deleted {count}")
    print(f"Reset {profile['full_name']}'s onboarding.")


if __name__ == "__main__":
    main()
