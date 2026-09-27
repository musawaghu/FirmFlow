"""Rate limits: keep one person, firm, or client from running up Claude costs or hammering the API.

Limits are sliding windows kept in memory, so they apply per backend process.
That is enough for one server; running several instances would need a shared
store such as Redis. Behind a proxy, start uvicorn with --proxy-headers so the
per-IP limit sees the real client address.

- Every /api request counts toward a per-IP limit (the middleware in main.py).
  This also caps how often an attacker can make us verify tokens with Supabase.
- Endpoints that call Claude also have per-user or per-firm limits
  (`Depends(rate_limit("chat"))`).
"""

from __future__ import annotations

import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, status

from app.auth import Profile, get_current_profile
from app.config import get_settings

MINUTE, HOUR, DAY = 60, 3600, 86400


@dataclass(frozen=True)
class Limit:
    count: int
    per_seconds: int
    scope: Literal["user", "firm", "ip"] = "user"


IP_LIMIT = Limit(300, MINUTE, "ip")

# Endpoint name -> limits that must all pass. Sized for real use with room to
# spare: a new hire asks a handful of questions, an admin processes a manual a
# few times a day.
LIMITS: dict[str, list[Limit]] = {
    "chat": [Limit(10, MINUTE), Limit(200, DAY)],
    "quiz_answer": [Limit(20, MINUTE)],  # scenario answers are graded by Claude
    "passage_edit": [Limit(60, HOUR, "firm")],  # edits re-run the grounding check
    "upload": [Limit(20, HOUR, "firm")],
    "process": [Limit(10, HOUR, "firm")],
    "detect_overrides": [Limit(10, HOUR, "firm")],
    "quiz_generate": [Limit(10, HOUR, "firm")],
}


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[tuple, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, keyed: list[tuple[tuple, Limit]], now: float | None = None) -> float | None:
        """Record one hit against every (key, limit), or none if any is full.

        Returns None if allowed, else the seconds until the fullest window frees up.
        """
        now = time.monotonic() if now is None else now
        with self._lock:
            waits = []
            for key, limit in keyed:
                hits = self._hits[key]
                while hits and hits[0] <= now - limit.per_seconds:
                    hits.popleft()
                if len(hits) >= limit.count:
                    waits.append(hits[0] + limit.per_seconds - now)
            if waits:
                return max(waits)
            for key, _ in keyed:
                self._hits[key].append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def too_many(retry_after: float) -> HTTPException:
    seconds = max(1, math.ceil(retry_after))
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Too many requests. Try again in {seconds} seconds.",
        headers={"Retry-After": str(seconds)},
    )


def check_ip(ip: str) -> float | None:
    if not get_settings().rate_limits_enabled:
        return None
    return limiter.check([(("ip", ip, IP_LIMIT.per_seconds), IP_LIMIT)])


def rate_limit(name: str):
    """Dependency that applies LIMITS[name] to the caller."""
    if name not in LIMITS:
        raise KeyError(f"No rate limit named {name!r}")

    def dependency(profile: Profile = Depends(get_current_profile)) -> None:
        if not get_settings().rate_limits_enabled:
            return
        keyed = [
            ((name, limit.per_seconds, profile.firm_id if limit.scope == "firm" else profile.id), limit)
            for limit in LIMITS[name]
        ]
        if (wait := limiter.check(keyed)) is not None:
            raise too_many(wait)

    return dependency
