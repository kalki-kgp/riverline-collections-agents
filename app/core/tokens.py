from __future__ import annotations

import json
from typing import Any

import tiktoken


TOTAL_CONTEXT_LIMIT = 2000
HANDOFF_CONTEXT_LIMIT = 500


class TokenBudgetError(ValueError):
    pass


def _encoding():
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoding().encode(text))


def count_json_tokens(payload: dict[str, Any]) -> int:
    return count_tokens(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def enforce_handoff_budget(summary_text: str, limit: int = HANDOFF_CONTEXT_LIMIT) -> int:
    tokens = count_tokens(summary_text)
    if tokens > limit:
        raise TokenBudgetError(f"handoff summary has {tokens} tokens; limit is {limit}")
    return tokens


def enforce_agent_context_budget(
    system_prompt: str,
    handoff_text: str = "",
    total_limit: int = TOTAL_CONTEXT_LIMIT,
    handoff_limit: int = HANDOFF_CONTEXT_LIMIT,
) -> dict[str, int]:
    system_tokens = count_tokens(system_prompt)
    handoff_tokens = count_tokens(handoff_text)
    total_tokens = system_tokens + handoff_tokens

    if handoff_tokens > handoff_limit:
        raise TokenBudgetError(f"handoff has {handoff_tokens} tokens; limit is {handoff_limit}")
    if total_tokens > total_limit:
        raise TokenBudgetError(f"agent context has {total_tokens} tokens; limit is {total_limit}")

    return {
        "system_prompt": system_tokens,
        "handoff": handoff_tokens,
        "total_context": total_tokens,
        "total_limit": total_limit,
        "handoff_limit": handoff_limit,
    }
