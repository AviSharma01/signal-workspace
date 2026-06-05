"""
make_backend — the single place that constructs a wrapped LLMBackend.

Every call to the Anthropic API goes through the CostGuard. There is no code
path that bypasses it. To add the local backend in a later slice, add a branch
here and nowhere else.
"""

from agent.llm.anthropic_backend import AnthropicBackend
from agent.llm.base import LLMBackend
from agent.llm.cost_guard import (
    CostGuard,
    SONNET_4_6_INPUT_PRICE_PER_TOKEN,
    SONNET_4_6_OUTPUT_PRICE_PER_TOKEN,
)


def make_backend(name: str = "anthropic") -> LLMBackend:
    """
    name: "anthropic"  — Anthropic API, wrapped in CostGuard (default)
          "local"      — local OpenAI-compatible server (slice 8)
    """
    if name == "anthropic":
        return CostGuard(
            backend=AnthropicBackend(),
            input_price_per_token=SONNET_4_6_INPUT_PRICE_PER_TOKEN,
            output_price_per_token=SONNET_4_6_OUTPUT_PRICE_PER_TOKEN,
        )

    raise ValueError(
        f"Unknown backend {name!r}. "
        "Supported: 'anthropic'. ('local' is implemented in slice 8.)"
    )
