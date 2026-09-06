from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Dimension(StrEnum):
    PROVINCE = "province"
    LINE_OF_BUSINESS = "line_of_business"
    UNDERWRITING_YEAR = "underwriting_year"


class ChartType(StrEnum):
    GROUPED_BAR = "grouped_bar"
    LINE = "line"
    TABLE = "table"


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
