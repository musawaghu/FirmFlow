"""An approved AEC baseline and firm A with an approved module that overrides it (A-101 vs. A1.01)."""

from tests.conftest import FIRM_A, FIRM_B

BASELINE = "b0000000-0000-4000-8000-000000000001"


def seed_layered(repo):
    """An approved baseline with two modules, and firm A with one approved module that renumbers sheets."""
    repo.insert("firms", [
        {"id": BASELINE, "name": "FIRM FLOW AEC Baseline", "slug": "firmflow-baseline", "is_baseline": True},
        {"id": FIRM_A, "name": "Studio Meridian Architects", "slug": "studio-meridian"},
        {"id": FIRM_B, "name": "Other Firm", "slug": "other"},
    ])
    base_manual = repo.insert("manuals", [{"firm_id": BASELINE, "title": "AEC Baseline Guide", "file_path": "b", "file_type": "pdf", "status": "processed"}])[0]
    base_section = repo.insert("source_sections", [{"manual_id": base_manual["id"], "ordinal": 1, "heading": "Drawing sets",
                                                    "content": "Number sheets like A1.01.", "page_start": 1, "page_end": 1}])[0]
    sets, consultants = repo.insert("modules", [
        {"firm_id": BASELINE, "manual_id": base_manual["id"], "title": "Drawing Set Organization", "ordinal": 0,
         "priority": "day_1", "status": "approved"},
        {"firm_id": BASELINE, "manual_id": base_manual["id"], "title": "Consultant Coordination", "ordinal": 1,
         "priority": "week_1", "status": "approved"},
    ])
    sheet, order, coord = repo.insert("module_passages", [
        {"module_id": sets["id"], "source_section_id": base_section["id"], "ordinal": 0, "heading": "Sheet numbers",
         "content": "Number sheets like A1.01: discipline, sheet type, sequence.", "kind": "text", "grounding_ok": True},
        {"module_id": sets["id"], "source_section_id": base_section["id"], "ordinal": 1, "heading": "Set order",
         "content": "General sheets come first.", "kind": "text", "grounding_ok": True},
        {"module_id": consultants["id"], "source_section_id": base_section["id"], "ordinal": 0, "heading": "Meetings",
         "content": "Attend coordination meetings.", "kind": "text", "grounding_ok": True},
    ])

    manual = repo.insert("manuals", [{"firm_id": FIRM_A, "title": "Handbook", "file_path": "a", "file_type": "pdf", "status": "processed"}])[0]
    section = repo.insert("source_sections", [{"manual_id": manual["id"], "ordinal": 1, "heading": "21. DRAWING STANDARDS",
                                               "content": "We number sheets A-101, never A1.01.", "page_start": 23, "page_end": 23}])[0]
    tech, draft = repo.insert("modules", [
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "Technology", "ordinal": 0, "priority": "day_1", "status": "approved"},
        {"firm_id": FIRM_A, "manual_id": manual["id"], "title": "Draft", "ordinal": 1, "priority": "day_1"},
    ])
    firm_sheet = repo.insert("module_passages", [
        {"module_id": tech["id"], "source_section_id": section["id"], "ordinal": 0, "heading": "Sheet numbering",
         "content": "Studio Meridian numbers sheets A-101, never A1.01.", "kind": "text", "grounding_ok": True},
    ])[0]
    override = repo.insert("baseline_overrides", [{
        "firm_id": FIRM_A, "manual_id": manual["id"], "firm_passage_id": firm_sheet["id"], "baseline_passage_id": sheet["id"],
        "firm_excerpt": "A-101, never A1.01", "baseline_excerpt": "A1.01", "difference": "Baseline A1.01; firm A-101.",
    }])[0]
    return {"sets": sets, "consultants": consultants, "sheet": sheet, "order": order, "coord": coord,
            "tech": tech, "firm_sheet": firm_sheet, "override": override, "manual": manual}
