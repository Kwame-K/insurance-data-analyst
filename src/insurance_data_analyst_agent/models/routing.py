from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from insurance_data_analyst_agent.models.analytics import LossRatioRequest


class ToolSelection(BaseModel):
    """A validated request to execute one allowed analytical tool."""

    model_config = ConfigDict(extra="forbid")

    tool_name: Literal["get_loss_ratio_by_segment"]
    arguments: LossRatioRequest
