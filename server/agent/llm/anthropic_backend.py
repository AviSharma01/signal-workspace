"""
AnthropicBackend — implements LLMBackend against the Anthropic Messages API.

API key loaded exclusively from server/.env via dotenv_values() — never read
from the OS environment, never logged (CLAUDE.md hard rule #5).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anthropic
from dotenv import dotenv_values

from agent.llm.base import LLMBackend, LLMResponse, ToolCall

# Current stable Sonnet model — verified at
# https://platform.claude.com/docs/en/docs/about-claude/models/overview
# on 2026-06-04. Update this constant when migrating to a newer model.
MODEL = "claude-sonnet-4-6"

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def _load_api_key() -> str:
    values = dotenv_values(_ENV_PATH)
    key = values.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            f"ANTHROPIC_API_KEY not found in {_ENV_PATH}. "
            "Add it to server/.env — never export it to the shell."
        )
    return key


def _to_anthropic_messages(messages: list[dict]) -> list[dict]:
    """Translate normalized messages to Anthropic's format.

    Normalized roles: "user" | "assistant" | "tool"
    Anthropic roles:  "user" | "assistant"
    Tool results become user messages containing tool_result content blocks.
    """
    out: list[dict] = []
    for msg in messages:
        role = msg["role"]

        if role == "user":
            out.append({"role": "user", "content": msg["content"]})

        elif role == "assistant":
            tool_calls: list[ToolCall] | None = msg.get("tool_calls")
            if tool_calls:
                content: list[dict] = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                out.append({"role": "assistant", "content": content})
            else:
                out.append({"role": "assistant", "content": msg.get("content", "")})

        elif role == "tool":
            # Tool results are user messages with tool_result blocks
            out.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg["tool_call_id"],
                    "content": msg["content"],
                }],
            })

    return out


def _to_anthropic_tools(tools: list[dict]) -> list[dict]:
    """Normalized tool schema uses input_schema — Anthropic accepts it directly."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in tools
    ]


class AnthropicBackend(LLMBackend):
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=_load_api_key())

    def complete(self, *, system: str, messages: list[dict],
                 tools: list[dict]) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": 4096,
            "system": system,
            "messages": _to_anthropic_messages(messages),
        }
        if tools:
            kwargs["tools"] = _to_anthropic_tools(tools)

        raw = self._client.messages.create(**kwargs)

        # Translate response blocks
        text: str | None = None
        tool_calls: list[ToolCall] = []
        for block in raw.content:
            if block.type == "text":
                text = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))

        stop_reason = "tool_use" if tool_calls else "end"

        # TODO: cache_creation_input_tokens and cache_read_input_tokens are
        # counted at the standard input rate here. Track them separately once
        # prompt caching is enabled.
        usage = {
            "input_tokens": raw.usage.input_tokens,
            "output_tokens": raw.usage.output_tokens,
        }

        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage=usage,
            raw=raw,
        )
