from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from insurance_data_analyst_agent.models.audit import (
    AgentRunAudit,
)


@dataclass(frozen=True)
class AuditWriter:
    """Persist agent audit records as versioned JSON files."""

    output_directory: Path

    def write(self, audit: AgentRunAudit) -> Path:
        """Write one audit record and return the generated file path."""
        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = audit.timestamp_utc.strftime("%Y%m%dT%H%M%S%fZ")

        output_path = self.output_directory / (f"{timestamp}_{audit.run_id}.json")

        temporary_path = output_path.with_suffix(".json.tmp")

        temporary_path.write_text(
            audit.model_dump_json(indent=2),
            encoding="utf-8",
        )

        temporary_path.replace(output_path)

        return output_path
