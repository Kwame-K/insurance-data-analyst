from __future__ import annotations

import re
import unicodedata

from insurance_data_analyst_agent.models.analytics import (
    Dimension,
    LossRatioRequest,
)
from insurance_data_analyst_agent.models.routing import ToolSelection


class UnsupportedQuestionError(ValueError):
    """Raised when a question cannot be mapped to an allowed tool."""


PROVINCE_ALIASES = {
    "quebec": "QC",
    "qc": "QC",
    "ontario": "ON",
    "british columbia": "BC",
    "colombie britannique": "BC",
    "alberta": "AB",
}

LINE_OF_BUSINESS_ALIASES = {
    "commercial property": "commercial_property",
    "propriete commerciale": "commercial_property",
    "commercial auto": "commercial_auto",
    "automobile commerciale": "commercial_auto",
    "general liability": "general_liability",
    "responsabilite civile generale": "general_liability",
}


def normalize_text(text: str) -> str:
    """Normalize whitespace, case, and French accents."""
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )

    return " ".join(without_accents.lower().split())


def extract_provinces(question: str) -> list[str] | None:
    """Extract recognized province filters from normalized text."""
    matched_provinces = [
        province_code
        for alias, province_code in PROVINCE_ALIASES.items()
        if re.search(rf"\b{re.escape(alias)}\b", question)
    ]

    unique_provinces = list(dict.fromkeys(matched_provinces))
    return unique_provinces or None


def extract_lines_of_business(question: str) -> list[str] | None:
    """Extract recognized line-of-business filters from normalized text."""
    matched_lines_of_business = [
        line_of_business
        for alias, line_of_business in LINE_OF_BUSINESS_ALIASES.items()
        if alias in question
    ]

    unique_lines_of_business = list(dict.fromkeys(matched_lines_of_business))
    return unique_lines_of_business or None


def extract_underwriting_years(
    question: str,
    available_years: list[int],
) -> list[int]:
    """Extract explicit years or resolve the last three available years."""
    requested_years = sorted(
        {int(year) for year in re.findall(r"\b20\d{2}\b", question)}
    )

    if requested_years:
        unavailable_years = [
            year for year in requested_years if year not in available_years
        ]

        if unavailable_years:
            unavailable_years_text = ", ".join(str(year) for year in unavailable_years)
            raise UnsupportedQuestionError(
                "Requested underwriting years are not available: "
                f"{unavailable_years_text}."
            )

        return requested_years

    requests_last_three_years = any(
        phrase in question
        for phrase in (
            "last three underwriting years",
            "last 3 underwriting years",
            "three latest underwriting years",
            "3 latest underwriting years",
            "trois dernieres annees de souscription",
            "3 dernieres annees de souscription",
        )
    )

    if requests_last_three_years:
        return available_years[-3:]

    return available_years[-3:]


def route_question(
    question: str,
    available_years: list[int],
) -> ToolSelection:
    """Route a supported question to a validated analytical tool call."""
    if not question.strip():
        raise UnsupportedQuestionError("Question must not be empty.")

    if not available_years:
        raise UnsupportedQuestionError(
            "No underwriting years are available in the portfolio database."
        )

    normalized_question = normalize_text(question)

    is_loss_ratio_question = any(
        phrase in normalized_question
        for phrase in (
            "loss ratio",
            "paid loss ratio",
            "ratio de sinistralite",
        )
    )

    if not is_loss_ratio_question:
        raise UnsupportedQuestionError(
            "Unsupported question. Currently supported analysis: "
            "loss ratio by province, line of business, and underwriting year."
        )

    underwriting_years = extract_underwriting_years(
        question=normalized_question,
        available_years=available_years,
    )

    return ToolSelection(
        tool_name="get_loss_ratio_by_segment",
        arguments=LossRatioRequest(
            underwriting_years=underwriting_years,
            dimensions=[
                Dimension.PROVINCE,
                Dimension.LINE_OF_BUSINESS,
                Dimension.UNDERWRITING_YEAR,
            ],
            provinces=extract_provinces(normalized_question),
            lines_of_business=extract_lines_of_business(normalized_question),
        ),
    )
