"""The one message shape every connector produces.

Nothing downstream knows which platform a message came from. Raw author IDs
never enter this model: connectors hash them with `hash_author` first.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

MIN_SALT_LENGTH = 16
AUTHOR_HASH_LENGTH = 16


class Source(str, Enum):
    SLACK = "slack"
    TEAMS = "teams"
    GCHAT = "gchat"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    FAKE = "fake"  # synthetic data, used for development and tests


def hash_author(raw_author_id: str, salt: str) -> str:
    """Stable, non-reversible pseudonym for a person.

    The same person always maps to the same value (so "distinct people" can be
    counted), but the value can't be turned back into a name or email without
    the salt, which never leaves the firm's environment.
    """
    if len(salt) < MIN_SALT_LENGTH:
        raise ValueError(f"author salt must be at least {MIN_SALT_LENGTH} characters")
    if not raw_author_id:
        raise ValueError("author id must not be empty")
    digest = hmac.new(salt.encode(), raw_author_id.encode(), hashlib.sha256).hexdigest()
    return digest[:AUTHOR_HASH_LENGTH]


class Message(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: Source
    source_id: str  # the configured source instance, e.g. "slack-main"
    channel: str  # channel, space, or mailbox label from the allowlist
    thread_id: str  # the message's own id when it isn't part of a thread
    message_id: str
    author_hash: str
    timestamp: datetime  # always timezone-aware UTC
    text: str

    @field_validator("author_hash")
    @classmethod
    def looks_hashed(cls, v: str) -> str:
        # Guards against a connector passing a raw user id, name, or email.
        ok = len(v) == AUTHOR_HASH_LENGTH and all(c in "0123456789abcdef" for c in v)
        if not ok:
            raise ValueError("author_hash must come from hash_author()")
        return v

    @field_validator("timestamp")
    @classmethod
    def utc_only(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return v.astimezone(timezone.utc)

    @field_validator("text")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        return v

    @field_validator("source_id", "channel", "thread_id", "message_id")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v
