"""One structured-output call to Claude, shared by the enhancer and grounding check."""

from __future__ import annotations

from typing import TypeVar

import anthropic
from anthropic.types.beta.parsed_beta_message import ParsedBetaMessage
from pydantic import BaseModel

from app.config import get_settings

FALLBACK_BETA = "server-side-fallback-2026-07-01"

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """The model call failed or returned something unusable."""


def structured_call(
    *,
    system: str,
    user: str,
    output_format: type[T],
    max_tokens: int,
    effort: str = "high",
    client: anthropic.Anthropic | None = None,
    model: str | None = None,
) -> tuple[T, ParsedBetaMessage[T]]:
    """Stream one request and return the parsed output plus the raw message (for usage)."""
    settings = get_settings()
    client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    model = model or settings.anthropic_model

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
            message = stream.get_final_message()
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
