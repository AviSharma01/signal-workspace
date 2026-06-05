from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end"          # "tool_use" | "end"
    # input_tokens and output_tokens so CostGuard stays provider-agnostic
    usage: dict[str, int] | None = None
    raw: Any = None                   # raw provider payload, for debugging


class LLMBackend(ABC):
    @abstractmethod
    def complete(self, *, system: str, messages: list[dict],
                 tools: list[dict]) -> LLMResponse:
        """messages and tools are in the normalized format defined in AGENT_SPEC.md §4.
        Each backend translates to/from its provider's native format."""
        ...
