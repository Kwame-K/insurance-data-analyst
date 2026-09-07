from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


class Dimension(StrEnum):
    PROVINCE = "province"
    LINE_OF_BUSINESS = "line_of_business"
    UNDERWRITING_YEAR = "underwriting_year"


class ChartType(StrEnum):
    GROUPED_BAR = "grouped_bar"
    LINE = "line"
    TABLE = "table"


ALLOWED_PROVINCES = {
    "QC",
    "ON",
    "BC",
    "AB",
}

ALLOWED_LINES_OF_BUSINESS = {
    "commercial_property",
    "commercial_auto",
    "general_liability",
}


class LossRatioRequest(BaseModel):
    underwriting_years: list[int] = Field(
        min_length=1,
        max_length=10,
        description="Underwriting years included in the analysis.",
    )
    dimensions: list[Dimension] = Field(
        default=[Dimension.PROVINCE, Dimension.LINE_OF_BUSINESS],
        min_length=1,
        max_length=3,
    )
    provinces: list[str] | None = None
    lines_of_business: list[str] | None = None

    @model_validator(mode="after")
    def validate_years(self) -> LossRatioRequest:
        if len(set(self.underwriting_years)) != len(self.underwriting_years):
            raise ValueError("underwriting_years must not contain duplicates.")

        if any(year < 2000 or year > 2100 for year in self.underwriting_years):
            raise ValueError("Each underwriting year must be between 2000 and 2100.")

        return self

    @field_validator("provinces")
    @classmethod
    def validate_provinces(
        cls,
        provinces: list[str] | None,
    ) -> list[str] | None:
        if provinces is None:
            return None

        invalid_provinces = [
            province for province in provinces if province not in ALLOWED_PROVINCES
        ]

        if invalid_provinces:
            raise ValueError(
                f"Unsupported province filters: {', '.join(invalid_provinces)}."
            )

        return provinces

    @field_validator("lines_of_business")
    @classmethod
    def validate_lines_of_business(
        cls,
        lines_of_business: list[str] | None,
    ) -> list[str] | None:
        if lines_of_business is None:
            return None

        invalid_lines_of_business = [
            line_of_business
            for line_of_business in lines_of_business
            if line_of_business not in ALLOWED_LINES_OF_BUSINESS
        ]

        if invalid_lines_of_business:
            raise ValueError(
                "Unsupported line-of-business filters: "
                f"{', '.join(invalid_lines_of_business)}."
            )

        return lines_of_business


class ToolCallAudit(BaseModel):
    tool_name: str
    validated_arguments: dict[str, Any]
    execution_status: Literal["success", "failed"]


class ChartMetadata(BaseModel):
    chart_type: ChartType
    x: str
    y: str
    series: list[str]
    title: str
    output_path: str | None = None


class AuditMetadata(BaseModel):
    dataset_version: str
    calculation_definition: str
    database_path: str


class AnalyticsResponse(BaseModel):
    question: str
    tool_calls: list[ToolCallAudit]
    raw_results: list[dict[str, Any]]
    answer: str
    chart: ChartMetadata | None = None
    audit: AuditMetadata
