from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from insurance_data_analyst_agent.services.router import (
    UnsupportedQuestionError,
    route_question,
)

AVAILABLE_YEARS = [2023, 2024, 2025]

CASES_PATH = Path(__file__).parent / "cases.json"

EVALUATION_CASES: list[dict[str, Any]] = json.loads(
    CASES_PATH.read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    "case",
    EVALUATION_CASES,
    ids=lambda case: str(case["id"]),
)
def test_router_evaluation_cases(
    case: dict[str, Any],
) -> None:
    question = str(case["question"])

    if "expected_error" in case:
        expected_error_message = str(case["expected_error_message"])

        with pytest.raises(
            UnsupportedQuestionError,
            match=expected_error_message,
        ):
            route_question(
                question=question,
                available_years=AVAILABLE_YEARS,
            )

        return

    selection = route_question(
        question=question,
        available_years=AVAILABLE_YEARS,
    )

    assert selection.tool_name == case["expected_tool_name"]

    assert selection.arguments.model_dump(mode="json") == (case["expected_arguments"])
