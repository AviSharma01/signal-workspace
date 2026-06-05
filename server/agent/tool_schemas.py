"""
Tool schemas (normalized §4 format) and TOOL_FUNCTIONS mapping.

Each schema follows: { "name", "description", "input_schema" (JSON Schema) }.
Descriptions tell the model *when* to use each tool, not just what it does.
TOOL_FUNCTIONS maps tool name → callable from agent/tools.py.
"""

from agent.tools import (
    get_discussion,
    get_news,
    get_price_movement,
    get_related_companies,
)

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_price_movement",
        "description": (
            "Quantify price and volume action for a ticker over a recent window. "
            "Call this first on the flagged ticker to establish the magnitude and "
            "direction of the move before looking for explanations. Also call it on "
            "sector peers to check for co-movement."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker symbol to query.",
                },
                "window_days": {
                    "type": "integer",
                    "description": "Number of calendar days of history to include. Defaults to 30.",
                    "default": 30,
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_news",
        "description": (
            "Retrieve recent news items for a ticker, newest first. "
            "Use to look for a causal headline — a story timed close to the anomalous bar. "
            "Only cite a news item as causal if its timestamp is near the move; "
            "stale items are distractors. Increase window_days only if the default "
            "window returns nothing and you have reason to believe news exists."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker symbol to query.",
                },
                "window_days": {
                    "type": "integer",
                    "description": "Number of calendar days before the most recent bar to search. Defaults to 7.",
                    "default": 7,
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_discussion",
        "description": (
            "Retrieve recent social/forum discussion for a ticker, newest first. "
            "Use after get_news when no causal headline is found. "
            "Look for unusual crowd activity timed to the anomalous move."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker symbol to query.",
                },
                "window_days": {
                    "type": "integer",
                    "description": "Number of calendar days before the most recent bar to search. Defaults to 7.",
                    "default": 7,
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_related_companies",
        "description": (
            "Return same-sector peers for a ticker (excludes the ticker itself). "
            "Use when news and discussion are absent or stale, to check whether "
            "the move is sector-wide rather than idiosyncratic. "
            "Follow up with get_price_movement on each peer to confirm co-movement."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The ticker symbol whose peers to retrieve.",
                },
            },
            "required": ["ticker"],
        },
    },
]

TOOL_FUNCTIONS: dict = {
    "get_price_movement":   get_price_movement,
    "get_news":             get_news,
    "get_discussion":       get_discussion,
    "get_related_companies": get_related_companies,
}
