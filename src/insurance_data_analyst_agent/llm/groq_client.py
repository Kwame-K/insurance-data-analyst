from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from groq import Groq

from insurance_data_analyst_agent.llm.base import (
    LLMClientError,
)


@dataclass
class GroqLLMClient:
    """Groq implementation of the provider-agnostic LLMClient protocol."""

    api_key: str
    model: str
    client: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = Groq(api_key=self.api_key)

    def generate_tool_selection(
        self,
        *,
        system_prompt: str,
        user_question: str,
    ) -> dict[str, Any]:
        """Request a JSON-compatible tool-selection candidate from Groq."""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_question,
                    },
                ],
                response_format={
                    "type": "json_object",
                },
                temperature=0,
            )
        except Exception as error:
            raise LLMClientError(f"Groq request failed: {error}") from error

        content = completion.choices[0].message.content

        if not content:
            raise LLMClientError("Groq returned an empty response.")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as error:
            raise LLMClientError("Groq returned invalid JSON.") from error

        if not isinstance(payload, dict):
            raise LLMClientError("Groq response must be a JSON object.")

        return payload
