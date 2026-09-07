from __future__ import annotations

from typing import Any, Protocol


class LLMClientError(RuntimeError):
    """Raised when an LLM provider cannot return a valid response."""


class LLMClient(Protocol):
    """Provider-agnostic interface for structured LLM generation."""

    def generate_tool_selection(
        self,
        *,
        system_prompt: str,
        user_question: str,
    ) -> dict[str, Any]:
        """Return a JSON-compatible tool-selection candidate."""
