from __future__ import annotations

from types import SimpleNamespace

import pytest

from insurance_data_analyst_agent.llm.base import (
    LLMClientError,
)
from insurance_data_analyst_agent.llm.groq_client import (
    GroqLLMClient,
)


class FakeGroqCompletions:
    def __init__(
        self,
        content: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.content = content
        self.error = error
        self.calls: list[dict] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=self.content,
                    )
                )
            ]
        )


class FakeGroqClient:
    def __init__(
        self,
        content: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.completions = FakeGroqCompletions(
            content=content,
            error=error,
        )
        self.chat = SimpleNamespace(
            completions=self.completions,
        )


def test_groq_client_returns_json_object() -> None:
    fake_client = FakeGroqClient(
        content="""
        {
          "tool_name": "get_loss_ratio_by_segment",
          "arguments": {
            "underwriting_years": [2025],
            "dimensions": [
              "province",
              "line_of_business",
              "underwriting_year"
            ],
            "provinces": ["QC"],
            "lines_of_business": ["commercial_property"]
          }
        }
        """
    )

    client = GroqLLMClient(
        api_key="test-key",
        model="test-model",
        client=fake_client,
    )

    response = client.generate_tool_selection(
        system_prompt="Return JSON only.",
        user_question="Show loss ratio for Quebec in 2025.",
    )

    assert response["tool_name"] == ("get_loss_ratio_by_segment")
    assert response["arguments"]["underwriting_years"] == [2025]

    request = fake_client.completions.calls[0]

    assert request["model"] == "test-model"
    assert request["temperature"] == 0
    assert request["response_format"] == {
        "type": "json_object",
    }


def test_groq_client_rejects_invalid_json() -> None:
    fake_client = FakeGroqClient(content="This is not valid JSON.")

    client = GroqLLMClient(
        api_key="test-key",
        model="test-model",
        client=fake_client,
    )

    with pytest.raises(
        LLMClientError,
        match="Groq returned invalid JSON",
    ):
        client.generate_tool_selection(
            system_prompt="Return JSON only.",
            user_question="Show loss ratio for Quebec in 2025.",
        )


def test_groq_client_rejects_empty_response() -> None:
    fake_client = FakeGroqClient(
        content=None,
    )

    client = GroqLLMClient(
        api_key="test-key",
        model="test-model",
        client=fake_client,
    )

    with pytest.raises(
        LLMClientError,
        match="Groq returned an empty response",
    ):
        client.generate_tool_selection(
            system_prompt="Return JSON only.",
            user_question="Show loss ratio for Quebec in 2025.",
        )


def test_groq_client_wraps_provider_errors() -> None:
    fake_client = FakeGroqClient(
        error=RuntimeError("Network unavailable."),
    )

    client = GroqLLMClient(
        api_key="test-key",
        model="test-model",
        client=fake_client,
    )

    with pytest.raises(
        LLMClientError,
        match="Groq request failed",
    ):
        client.generate_tool_selection(
            system_prompt="Return JSON only.",
            user_question="Show loss ratio for Quebec in 2025.",
        )
