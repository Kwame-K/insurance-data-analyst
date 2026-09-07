from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from insurance_data_analyst_agent.llm.base import (
    LLMClientError,
)


@dataclass
class FakeLLMClient:
    """Deterministic fake LLM client used in unit and integration tests."""

    response: dict[str, Any] | None = None
    error: Exception | None = None
    calls: list[dict[str, str]] = field(default_factory=list)

    def generate_tool_selection(
        self,
        *,
        system_prompt: str,
        user_question: str,
    ) -> dict[str, Any]:
        """Return a configured response or raise a configured error."""
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_question": user_question,
            }
        )

        if self.error is not None:
            raise self.error

        if self.response is None:
            raise LLMClientError("FakeLLMClient has no configured response.")

        return deepcopy(self.response)
