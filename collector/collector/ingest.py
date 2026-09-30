"""Daily incremental ingest: fetch only what's new, hand it on, then move the cursor.

The cursor is saved only after the handler has accepted a page, so a crash
between the two re-delivers that page instead of losing it (at-least-once).
Handlers should tolerate seeing a message twice.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from collector.connectors.base import Connector
from collector.schema import Message
from collector.sync_state import SyncState

log = logging.getLogger(__name__)

Handler = Callable[[list[Message]], None]

DEFAULT_PAGE_SIZE = 200
DEFAULT_MAX_PAGES = 1000


@dataclass
class IngestStats:
    pages: int = 0
    messages: int = 0
    error: str | None = None  # the exception type only, never message content


def ingest_channel(
    connector: Connector,
    state: SyncState,
    channel: str,
    handler: Handler,
    *,
    since: datetime | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> IngestStats:
    stats = IngestStats()
    cursor = state.get(connector.source_id, channel)
    while stats.pages < max_pages:
        result = connector.fetch_new(channel, cursor, since=since, limit=page_size)
        if result.messages:
            handler(result.messages)
        stats.pages += 1
        stats.messages += len(result.messages)
        if result.cursor is not None:
            state.set(connector.source_id, channel, result.cursor)
        if not result.has_more:
            return stats
        if result.cursor is None or result.cursor == cursor:
            # More pages promised but no progress: stop rather than loop forever.
            raise RuntimeError(f"{connector.source_id}/{channel}: cursor did not advance while more pages remain")
        cursor = result.cursor
    log.warning("%s/%s: stopped after %d pages; the rest will be picked up next run", connector.source_id, channel, max_pages)
    return stats


def ingest_source(
    connector: Connector,
    state: SyncState,
    handler: Handler,
    *,
    since: datetime | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> dict[str, IngestStats]:
    """Ingest every allowlisted channel. One failing channel doesn't block the rest."""
    out: dict[str, IngestStats] = {}
    for channel in connector.channels:
        try:
            out[channel] = ingest_channel(
                connector, state, channel, handler, since=since, page_size=page_size, max_pages=max_pages
            )
        except Exception as exc:  # noqa: BLE001 - isolate channels from each other
            log.error("%s/%s failed: %s", connector.source_id, channel, type(exc).__name__)
            out[channel] = IngestStats(error=type(exc).__name__)
    return out
