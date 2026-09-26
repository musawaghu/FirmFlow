"""Run the enhancer and grounding check on the sample manual.

Scores the issues against samples/PLANTED_ISSUES.md and lists passages the
grounding check flagged.

Calls the Claude API (costs real tokens). From backend/:
    .venv/bin/python -m scripts.enhance_sample [--out enhancement_sample.json]
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from app.services.enhancer import enhance_manual
from app.services.grounding import check_enhancement
from app.services.parser import parse_manual

SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "studio_meridian_manual.pdf"
DEMO_MODULES = [
    "Timesheets",
    "Staff Directory",
    "Company Policies & Workplace Etiquette",
    "How to Use BIM",
    "PTO",
    "Privacy & Harassment Training",
]
PRICE_PER_MTOK = {"claude-opus-5": (5.00, 25.00)}

# (id, accepted issue types, heading must contain, excerpt must contain one of)
PLANTED = [
    ("B1", {"broken_link"}, "Staff Directory", ["intranet.studiomeridian.example/staff"]),
    ("B2", {"broken_link"}, "BIM", ["SM-FS01"]),
    ("B3", {"broken_link", "outdated_reference"}, "TIMESHEETS", ["intranet homepage"]),
    ("B4", {"broken_link"}, "PTO", ["go/pto-form"]),
    ("B5", {"broken_link"}, "HARASSMENT", ["ethicsline"]),
    ("O1", {"outdated_reference", "contradiction"}, "BIM", ["Revit 2019"]),
    ("O2", {"outdated_reference"}, "TIMESHEETS", ["Log in to Deltek Vision", "Deltek Vision from"]),
    ("O3", {"outdated_reference"}, "TIMESHEETS", ["Internet Explorer"]),
    ("O4", {"outdated_reference"}, "HARASSMENT", ["DVD", "2017 harassment"]),
    ("C1", {"contradiction"}, "BIM", ["Revit 2019", "Revit 2025"]),
    ("C2", {"contradiction"}, "ETIQUETTE", ["10:00 AM to 4:00 PM", "9:30 AM to 3:30 PM"]),
    ("C3", {"contradiction"}, "TIMESHEETS", ["Friday by 5:00", "Monday at 12:00"]),
    ("C4", {"contradiction"}, "PTO", ["15 days", "10 days"]),
    ("C5", {"contradiction"}, "PTO", ["two weeks", "5 business days"]),
    ("C6", {"contradiction"}, "HARASSMENT", ["every two years", "annually"]),
    ("M1", {"missing_step"}, "TIMESHEETS", [""]),
    ("M2", {"missing_step"}, "Requesting time off", [""]),
]


def score(result, sections):
    headings = {s.ordinal: s.heading or "" for s in sections}
    found, missed = [], []
    for pid, types, heading, needles in PLANTED:
        hit = any(
            i.type in types
            and heading.lower() in headings[i.source_section_id].lower()
            and any(n.lower() in i.excerpt.lower() for n in needles)
            for i in result.issues
        )
        (found if hit else missed).append(pid)
    return found, missed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="enhancement_sample.json")
    args = parser.parse_args()

    parsed = parse_manual(SAMPLE.read_bytes(), "pdf")
    sections = parsed.sections
    print(f"Parsed {len(sections)} sections from {parsed.page_count} pages. Calling Claude...", flush=True)

    result = enhance_manual(sections, module_topics=DEMO_MODULES)
    headings = {s.ordinal: s.heading for s in sections}

    print(f"\n== Modules ({len(result.modules)})")
    for m in result.modules:
        cited = sorted({p.source_section_id for p in m.passages})
        print(f"- {m.title} [{m.suggested_priority}] {len(m.passages)} passages from sections {cited}")

    print(f"\n== Issues ({len(result.issues)})")
    for i in result.issues:
        related = f" <-> [{i.related_section_id}]" if i.related_section_id is not None else ""
        print(f"- {i.type} [{i.source_section_id}]{related} {i.excerpt!r}\n    {i.description}")

    print("\n== Left out of every module")
    for sid in result.unused_section_ids:
        print(f"- [{sid}] {headings[sid]}")

    if result.warnings:
        print("\n== Validation warnings")
        for w in result.warnings:
            print(f"- {w}")

    print("\n== Grounding check...", flush=True)
    grounded = check_enhancement(result, sections)
    for key, g in grounded.passages.items():
        if g.grounding_ok:
            continue
        mi, pi = map(int, key.split("."))
        passage = result.modules[mi].passages[pi]
        print(f"- {result.modules[mi].title} / passage {pi} (section {passage.source_section_id})")
        for span in g.unsupported_spans:
            where = "" if span.located else " [quote not found in passage]"
            print(f"    {span.check}: {span.text!r}: {span.reason}{where}")
    total = len(grounded.passages)
    print(f"{total - len(grounded.flagged)}/{total} passages fully grounded")
    if grounded.omissions:
        print("Facts from a section that no passage kept:")
        for o in grounded.omissions:
            print(f"- [{o.section_id}] {o.text!r}")
    for w in grounded.warnings:
        print(f"- warning: {w}")

    found, missed = score(result, sections)
    print(f"\n== Planted issues found: {len(found)}/{len(PLANTED)}")
    if missed:
        print(f"Missed: {', '.join(missed)}")

    input_tokens = result.input_tokens + grounded.input_tokens
    output_tokens = result.output_tokens + grounded.output_tokens
    price = PRICE_PER_MTOK.get(result.model)
    cost = f" (~${input_tokens / 1e6 * price[0] + output_tokens / 1e6 * price[1]:.2f})" if price else ""
    print(f"\n{result.model}: {input_tokens} input / {output_tokens} output tokens{cost}")

    Path(args.out).write_text(json.dumps(
        {
            "modules": [m.model_dump() for m in result.modules],
            "issues": [i.model_dump() for i in result.issues],
            **{k: v for k, v in asdict(result).items() if k not in ("modules", "issues")},
            "grounding": {
                "passages": {k: [s.to_json() for s in g.unsupported_spans] for k, g in grounded.passages.items()},
                "omissions": [asdict(o) for o in grounded.omissions],
                "warnings": grounded.warnings,
            },
        },
        indent=2,
    ))
    print(f"Full output written to {args.out}")
    return 0 if not missed else 1


if __name__ == "__main__":
    sys.exit(main())
