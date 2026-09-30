from __future__ import annotations

from datetime import datetime, timezone

from collector.connectors.base import Connector, FetchResult
from collector.schema import Message, Source, hash_author

SALT = "test-salt-0123456789"


def make_message(n: int, *, channel: str = "C1", source_id: str = "fake-1", source: Source = Source.FAKE) -> Message:
    return Message(
        source=source,
        source_id=source_id,
        channel=channel,
        thread_id=f"t{n}",
        message_id=f"m{n}",
        author_hash=hash_author(f"user{n}", SALT),
        timestamp=datetime(2026, 9, 1, 12, n % 60, tzinfo=timezone.utc),
        text=f"message number {n}",
    )


class ScriptedConnector(Connector):
    """Serves a fixed list of pages per channel. A page is (messages, cursor, has_more)."""

    source = Source.FAKE

    def __init__(self, pages: dict[str, list[FetchResult]], source_id: str = "fake-1"):
        super().__init__(source_id, pages.keys())
        self._pages = pages
        self.calls: list[tuple[str, str | None]] = []

    def _fetch_new(self, channel, cursor, *, since, limit):
        self.calls.append((channel, cursor))
        pages = self._pages[channel]
        # The page to serve is the one after the page whose cursor the caller holds.
        if cursor is None:
            idx = 0
        else:
            idx = next(i for i, p in enumerate(pages) if p.cursor == cursor) + 1
        if idx >= len(pages):
            return FetchResult(messages=[], cursor=cursor, has_more=False)
        return pages[idx]
