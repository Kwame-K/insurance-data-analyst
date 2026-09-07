from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from insurance_data_analyst_agent.models.analytics import (
    AnalyticsResponse,
    ToolCallAudit,
)


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(UTC)


class ErrorAudit(BaseModel):
    """Serializable representation of a controlled or unexpected error."""

    error_type: str
    message: str


class AgentRunAudit(BaseModel):
    """Complete persistent audit record for one agent execution."""

    run_id: UUID = Field(default_factory=uuid4)
    timestamp_utc: datetime = Field(default_factory=utc_now)

    agent_version: str
    dataset_version: str
    database_path: str

    question: str
    status: Literal["success", "failed"]

    tool_calls: list[ToolCallAudit] = Field(default_factory=list)
    raw_results: list[dict[str, Any]] = Field(default_factory=list)

    final_response: AnalyticsResponse | None = None
    error: ErrorAudit | None = None
