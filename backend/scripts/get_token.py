"""Log in as a demo user and print a Supabase access token for calling the API.

Reads SUPABASE_URL and SUPABASE_ANON_KEY from backend/.env and asks for the password.
From backend/:
    TOKEN=$(.venv/bin/python -m scripts.get_token)                          # Priya (admin)
    TOKEN=$(.venv/bin/python -m scripts.get_token alex.rivera@studiomeridian.example)
"""

import getpass
import sys

import httpx

from app.config import get_settings

DEFAULT_EMAIL = "priya.raman@studiomeridian.example"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    settings = get_settings()
    url = settings.supabase_url.strip().rstrip("/")
    key = settings.supabase_anon_key.strip()
    if not url.startswith("https://") or not url.endswith(".supabase.co"):
        fail(f"SUPABASE_URL in backend/.env should be just https://<ref>.supabase.co, with no path like /rest/v1 (got {url!r})")
    if not key:
        fail("Set SUPABASE_ANON_KEY in backend/.env to the legacy 'anon public' key")
    if key == settings.supabase_service_role_key.strip():
        fail("SUPABASE_ANON_KEY is the same as the service role key; use the 'anon public' key")

    email = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
    password = getpass.getpass(f"Password for {email}: ")
    response = httpx.post(
        f"{url}/auth/v1/token?grant_type=password",
        headers={"apikey": key},
        json={"email": email, "password": password},
        timeout=20,
    )
    if response.status_code != 200:
        fail(f"Supabase said ({response.status_code}): {response.text}")
    print(response.json()["access_token"])


if __name__ == "__main__":
    main()
