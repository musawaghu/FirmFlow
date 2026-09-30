"""Connector interface.

Every platform adapter (Slack, Teams, Gmail, ...) implements `_fetch_new`.
Callers use `fetch_new`, which enforces the channel allowlist and checks the
adapter's output, so a buggy or overly broad adapter can't read, or hand back,
anything outside what the firm approved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Iterable

from collector.schema import Message, Source


class ConnectorError(Exception):
    """A connector failed or returned something it shouldn't have."""


class ChannelNotAllowed(ConnectorError):
    """Asked for a channel that is not on the firm's allowlist."""


@dataclass(frozen=True)
class FetchResult:
    messages: list[Message] = field(default_factory=list)
    # Opaque, platform-specific position (a Slack ts, a Graph delta link, a Gmail
    # historyId). Pass it back on the next call. None means "nothing to record".
    cursor: str | None = None
    has_more: bool = False


class Connector(ABC):
    source: ClassVar[Source]

    def __init__(self, source_id: str, channels: Iterable[str]):
        allowed = tuple(dict.fromkeys(c for c in channels if c and c.strip()))
        if not allowed:
            raise ValueError("a connector needs a non-empty channel allowlist")
        self.source_id = source_id
        self._channels = allowed

    @property
    def channels(self) -> tuple[str, ...]:
        return self._channels

    def fetch_new(
        self,
        channel: str,
        cursor: str | None,
        *,
        since: datetime | None = None,
        limit: int = 200,
    ) -> FetchResult:
        """Fetch one page of messages newer than `cursor`.

        `since` only applies on the first run (cursor is None) and bounds how far
        back to look. Afterwards the cursor alone decides.
        """
        if channel not in self._channels:
            raise ChannelNotAllowed(f"{channel!r} is not on the allowlist for {self.source_id}")
        result = self._fetch_new(channel, cursor, since=since, limit=limit)
        for m in result.messages:
            if m.channel != channel or m.source_id != self.source_id or m.source != self.source:
                raise ConnectorError(f"{self.source_id} returned a message that does not belong to {channel!r}")
        return result

    @abstractmethod
    def _fetch_new(
        self,
        channel: str,
        cursor: str | None,
        *,
        since: datetime | None,
        limit: int,
    ) -> FetchResult: ...
