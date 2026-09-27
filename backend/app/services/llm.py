"""One structured-output call to Claude, shared by the enhancer, grounding check, overrides, and quiz.

Every call is bounded. The SDK default (10-minute read timeout, 2 retries) let
a stalled stream hang a request for about half an hour, so the client here
gives up when the stream goes silent for READ_TIMEOUT, retries once, and each
call also has a wall-clock deadline checked as events arrive.
"""

from __future__ import annotations

import time
from typing import TypeVar

import anthropic
from anthropic.types.beta.parsed_beta_message import ParsedBetaMessage
from pydantic import BaseModel

from app.config import get_settings

FALLBACK_BETA = "server-side-fallback-2026-07-01"

CONNECT_TIMEOUT = 10.0
# Longest silence allowed between bytes of a response. A healthy stream keeps
# sending events (including pings) while the model thinks, so this only trips
# on a dead connection.
READ_TIMEOUT = 180.0
MAX_RETRIES = 1
DEFAULT_DEADLINE = 600.0  # seconds for one whole call, retries excluded

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """The model call failed or returned something unusable."""


def claude_client() -> anthropic.Anthropic:
    """The Claude client every service uses, with bounded timeouts and retries."""
    settings = get_settings()
    return anthropic.Anthropic(
        api_key=settings.anthropic_api_key or None,
        timeout=anthropic.Timeout(READ_TIMEOUT, connect=CONNECT_TIMEOUT),
        max_retries=MAX_RETRIES,
    )


def structured_call(
    *,
    system: str,
    user: str,
    output_format: type[T],
    max_tokens: int,
    effort: str = "high",
    client: anthropic.Anthropic | None = None,
    model: str | None = None,
    deadline: float = DEFAULT_DEADLINE,
) -> tuple[T, ParsedBetaMessage[T]]:
    """Stream one request and return the parsed output plus the raw message (for usage).

    Raises LLMError if the whole call takes longer than `deadline` seconds.
    """
    settings = get_settings()
    client = client or claude_client()
    model = model or settings.anthropic_model
    started = time.monotonic()

    try:
        with client.beta.messages.stream(
            model=model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            output_format=output_format,
            betas=[FALLBACK_BETA],
            fallbacks="default",  # re-run a safety refusal on a fallback model server-side
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for _event in stream:
                if time.monotonic() - started > deadline:
                    raise LLMError(f"The model took longer than {deadline:.0f} seconds")
            message = stream.get_final_message()
    except anthropic.APITimeoutError as exc:
        raise LLMError("The Claude API stopped responding") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMError(f"Could not reach the Claude API: {exc}") from exc
    except anthropic.APIStatusError as exc:
        raise LLMError(f"Claude API error {exc.status_code}: {exc.message}") from exc
    except ValueError as exc:  # includes pydantic.ValidationError, e.g. partial output after a refusal
        raise LLMError("The model returned output that could not be read") from exc

    if message.stop_reason == "refusal":
        raise LLMError("The model declined to process this request")
    if message.stop_reason == "max_tokens":
        raise LLMError("The input is too long to process in one pass")
    parsed = message.parsed_output
    if parsed is None:
        raise LLMError(f"The model returned no structured output (stop reason: {message.stop_reason})")
    return parsed, message
