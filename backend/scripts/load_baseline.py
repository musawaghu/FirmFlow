"""Load the FIRM FLOW AEC Baseline Guide as the shared baseline every firm sees.

The guide goes through the same pipeline as a firm manual (parse, enhance,
grounding check), under the baseline firm. Its modules stay drafts until a
licensed architect has reviewed them, then --approve publishes them to every firm.

Calls the Claude API (costs real tokens). From backend/:
    .venv/bin/python -m scripts.load_baseline              # upload and process, print for review
    .venv/bin/python -m scripts.load_baseline --show       # print the current baseline again
    .venv/bin/python -m scripts.load_baseline --approve    # after review: approve every draft module
"""

import argparse
import sys
import uuid
from pathlib import Path

from app.db import get_repo, get_storage
from app.services.parser import parse_manual
from app.services.processing import has_approved_modules, process_manual, save_sections

GUIDE = Path(__file__).resolve().parents[2] / "samples" / "aec_baseline_guide.pdf"
TOPICS = [
    "Getting Started at an AEC Firm: software access, getting help, where information lives, drawing standards",
    "Revit Worksharing Basics: central and local models, daily rules, test copies",
    "BIM Execution Plans: what a BEP covers and how to work with it",
    "File Naming Conventions",
    "Drawing Set Organization: sheet numbers, set order, revisions",
    "Consultant Coordination",
]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def baseline(repo):
    firm = repo.select_one("firms", {"is_baseline": True})
    if firm is None:
        fail("No baseline firm. Run supabase/migrations/002_baseline_overlay.sql first.")
    manuals = repo.select("manuals", {"firm_id": firm["id"]}, order="created_at")
    return firm, (manuals[-1] if manuals else None)


def show(repo, manual) -> None:
    notes = manual.get("processing_notes") or {}
    print(f"\n{manual['title']}: {manual['status']}"
          f" ({notes.get('input_tokens', 0)} input / {notes.get('output_tokens', 0)} output tokens)")
    if manual.get("error"):
        print("Error:", manual["error"])
    for w in notes.get("warnings", []):
        print("Warning:", w)
    for m in repo.select("modules", {"manual_id": manual["id"]}, order="ordinal"):
        print(f"\n=== {m['title']} [{m['status']}, {m['priority']}]\n{m['summary'] or ''}")
        for p in repo.select("module_passages", {"module_id": m["id"]}, order="ordinal"):
            flag = "" if p["grounding_ok"] else f"  !! NOT GROUNDED: {[s['text'] for s in p['unsupported_spans']]}"
            print(f"\n--- {p['heading'] or '(no heading)'} [{p['kind']}]{flag}\n{p['content']}")
    issues = repo.select("issues", {"manual_id": manual["id"]})
    if issues:
        print("\n=== Issues flagged in the guide")
        for i in issues:
            print(f"- [{i['type']}] {i['description']}")


def load(repo, storage, firm) -> None:
    data = GUIDE.read_bytes()
    parsed = parse_manual(data, "pdf")
    manual_id = str(uuid.uuid4())
    path = f"{firm['id']}/{manual_id}.pdf"
    storage.upload(path, data, "application/pdf")
    manual = repo.insert("manuals", [{
        "id": manual_id, "firm_id": firm["id"], "title": "FIRM FLOW AEC Baseline Guide", "file_path": path,
        "file_type": "pdf", "page_count": parsed.page_count, "status": "processing",
    }])[0]
    save_sections(repo, manual_id, parsed)
    print(f"Parsed {len(parsed.sections)} sections from {parsed.page_count} pages. Calling Claude...", flush=True)
    process_manual(repo, manual, TOPICS)
    show(repo, repo.select_one("manuals", {"id": manual_id}))


def approve(repo, manual) -> None:
    drafts = repo.select("modules", {"manual_id": manual["id"], "status": "draft"})
    if not drafts:
        fail("No draft baseline modules to approve.")
    flagged = [
        m["title"] for m in drafts
        if any(not p["grounding_ok"] for p in repo.select("module_passages", {"module_id": m["id"]}))
    ]
    if flagged:
        fail(f"Fix or review the ungrounded passages first: {', '.join(flagged)}")
    for m in drafts:
        repo.update("modules", m["id"], {"status": "approved"})
        print(f"Approved {m['title']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--approve", action="store_true")
    args = parser.parse_args()

    repo = get_repo()
    firm, manual = baseline(repo)
    if args.show or args.approve:
        if manual is None:
            fail("The baseline hasn't been loaded yet.")
        approve(repo, manual) if args.approve else show(repo, manual)
        return
    if manual is not None and has_approved_modules(repo, manual["id"]):
        fail("The baseline is already approved. Loading a new version would replace what every firm sees.")
    if manual is not None:
        fail(f"A baseline draft already exists ({manual['id']}). Review it with --show, or delete it before loading again.")
    load(repo, get_storage(), firm)


if __name__ == "__main__":
    main()
