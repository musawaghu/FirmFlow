"""Per-channel cursors, kept in a local SQLite file.

What the collector has read is never stored in the hosted backend.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class SyncState:
    def __init__(self, path: str | Path):
        self._db = sqlite3.connect(str(path))
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                source_id  TEXT NOT NULL,
                channel    TEXT NOT NULL,
                cursor     TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (source_id, channel)
            )
            """
        )
        self._db.commit()

    def get(self, source_id: str, channel: str) -> str | None:
        row = self._db.execute(
            "SELECT cursor FROM sync_state WHERE source_id = ? AND channel = ?", (source_id, channel)
        ).fetchone()
        return row[0] if row else None

    def set(self, source_id: str, channel: str, cursor: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._db.execute(
            """
            INSERT INTO sync_state (source_id, channel, cursor, updated_at) VALUES (?, ?, ?, ?)
            ON CONFLICT (source_id, channel) DO UPDATE SET cursor = excluded.cursor, updated_at = excluded.updated_at
            """,
            (source_id, channel, cursor, now),
        )
        self._db.commit()

    def reset(self, source_id: str, channel: str | None = None) -> None:
        """Forget a cursor (or all of a source's cursors) so the next run starts over."""
        if channel is None:
            self._db.execute("DELETE FROM sync_state WHERE source_id = ?", (source_id,))
        else:
            self._db.execute("DELETE FROM sync_state WHERE source_id = ? AND channel = ?", (source_id, channel))
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "SyncState":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
