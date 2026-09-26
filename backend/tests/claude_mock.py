"""Run the real Anthropic SDK against canned streaming responses."""

import itertools
import json

import anthropic
import httpx2


def sse(payload=None, stop_reason="end_turn", input_tokens=1200, output_tokens=850) -> str:
    """A streamed message whose single text block is `payload` as JSON."""
    text = json.dumps(payload) if payload is not None else ""
    events = [
        ("message_start", {"type": "message_start", "message": {
            "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5",
            "content": [], "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": input_tokens, "output_tokens": 1},
        }}),
        ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        ("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                           "usage": {"output_tokens": output_tokens}}),
        ("message_stop", {"type": "message_stop"}),
    ]
    return "".join(f"event: {name}\ndata: {json.dumps(data)}\n\n" for name, data in events)


def message(*content, stop_reason="end_turn", input_tokens=500, output_tokens=60) -> str:
    """A non-streamed message. Pass content blocks from `text_json()` and `tool_use()`."""
    return json.dumps({
        "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5",
        "content": list(content), "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    })


def text_json(payload) -> dict:
    return {"type": "text", "text": json.dumps(payload)}


def tool_use(name: str, tool_input: dict, id: str = "toolu_1") -> dict:
    return {"type": "tool_use", "id": id, "name": name, "input": tool_input}


def mock_client(bodies, requests: list | None = None) -> anthropic.Anthropic:
    """Client that answers requests with `bodies` (one str, or a list cycled in order).

    Bodies from `sse()` are served as a stream, bodies from `message()` as JSON.
    """
    replies = itertools.cycle([bodies] if isinstance(bodies, str) else list(bodies))
    requests = requests if requests is not None else []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        body = next(replies)
        content_type = "text/event-stream" if body.startswith("event:") else "application/json"
        return httpx2.Response(200, headers={"content-type": content_type}, content=body.encode())

    return anthropic.Anthropic(
        api_key="test",
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )


def error_client(status: int, message: str = "bad") -> anthropic.Anthropic:
    def handler(request):
        return httpx2.Response(status, json={"type": "error", "error": {"type": "invalid_request_error", "message": message}})

    return anthropic.Anthropic(
        api_key="test",
        max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
