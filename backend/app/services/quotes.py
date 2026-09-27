"""Finding a model's quote in the text it claims to quote."""

from __future__ import annotations

import re


def locate_quote(quote: str, *texts: str) -> str | None:
    """The quote as it appears in the first of `texts` that contains it.

    Tolerates case and whitespace differences, and returns the matching text
    as the source spells it so it can be highlighted. An empty or
    whitespace-only quote is never found.
    """
    words = quote.split()
    if not words:
        return None
    for text in texts:
        if quote in text:
            return quote
    pattern = re.compile(r"\s+".join(re.escape(w) for w in words), re.IGNORECASE)
    for text in texts:
        if m := pattern.search(text):
            return m.group()
    return None
