"""In-memory stand-ins for Repo and Storage."""

import copy
import itertools
import uuid
from datetime import datetime, timedelta, timezone

from app.db import Filters, Row

# Column defaults from supabase/schema.sql that the code relies on reading back.
DEFAULTS = {
    "manuals": {"error": None, "page_count": None, "processing_notes": {}},
    "modules": {"summary": None, "is_required": True, "status": "draft", "priority": "later"},
    "module_passages": {"is_critical": False, "grounding_ok": None, "unsupported_spans": []},
    "issues": {"status": "open", "module_id": None, "source_section_id": None, "related_section_id": None, "excerpt": None},
    "quiz_questions": {"status": "draft", "choices": None, "correct_choice": None, "rubric": None},
    "quiz_attempts": {"status": "in_progress", "score": None, "completed_at": None, "question_ids": []},
    "quiz_answers": {"try_number": 1, "selected_choice": None, "answer_text": None, "feedback": None},
    "firms": {"is_baseline": False, "default_contact_id": None, "timezone": "America/Los_Angeles"},
    "firm_baseline_modules": {"priority": None, "is_required": None, "ordinal": None, "is_hidden": False},
    "firm_baseline_passages": {"is_critical": False},
    "baseline_overrides": {"status": "proposed", "manual_id": None, "reviewed_by": None, "reviewed_at": None},
}


class FakeRepo:
    def __init__(self):
        self.tables: dict[str, list[Row]] = {}
        self._clock = itertools.count()
        self.fail_on_insert: str | None = None  # table name that raises on insert

    def _match(self, row: Row, filters: Filters) -> bool:
        for column, value in filters.items():
            if isinstance(value, list):
                if row.get(column) not in value:
                    return False
            elif row.get(column) != value:
                return False
        return True

    def select(self, table, filters=None, order=None):
        rows = [copy.deepcopy(r) for r in self.tables.get(table, []) if self._match(r, filters or {})]
        if order:
            rows.sort(key=lambda r: r[order])
        return rows

    def select_one(self, table, filters):
        rows = self.select(table, filters)
        return rows[0] if rows else None

    def insert(self, table, rows):
        if table == self.fail_on_insert:
            raise RuntimeError(f"insert into {table} failed")
        stored = []
        for row in rows:
            now = datetime(2026, 9, 28, tzinfo=timezone.utc) + timedelta(seconds=next(self._clock))
            full = {"id": str(uuid.uuid4()), "created_at": now.isoformat(), **copy.deepcopy(DEFAULTS.get(table, {})), **row}
            self.tables.setdefault(table, []).append(full)
            stored.append(copy.deepcopy(full))
        return stored

    def update(self, table, row_id, fields):
        for row in self.tables.get(table, []):
            if row["id"] == row_id:
                row.update(copy.deepcopy(fields))
                return copy.deepcopy(row)
        return None

    def delete(self, table, filters):
        if not filters:
            raise ValueError("Refusing to delete without a filter")
        self.tables[table] = [r for r in self.tables.get(table, []) if not self._match(r, filters)]
        if table == "manuals":  # emulate on delete cascade
            ids = {r["id"] for r in self.tables["manuals"]}
            self.tables["source_sections"] = [s for s in self.tables.get("source_sections", []) if s["manual_id"] in ids]


class FakeStorage:
    def __init__(self):
        self.files: dict[str, tuple[bytes, str]] = {}

    def upload(self, path, data, content_type):
        self.files[path] = (data, content_type)

    def remove(self, path):
        self.files.pop(path, None)
