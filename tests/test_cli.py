from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from insurance_data_analyst_agent.cli import app

runner = CliRunner()


def test_init_data_creates_database(tmp_path: Path) -> None:
    database_path = tmp_path / "portfolio.db"

    result = runner.invoke(
        app,
        [
            "init-data",
            "--database-path",
            str(database_path),
            "--seed",
            "42",
        ],
    )

    assert result.exit_code == 0
    assert database_path.exists()

    payload = json.loads(result.stdout)

    assert payload["status"] == "success"
    assert payload["database_path"] == str(database_path)
    assert payload["seed"] == 42
    assert payload["dataset_version"] == "synthetic-v1"


def test_loss_ratio_returns_auditable_json(tmp_path: Path) -> None:
    database_path = tmp_path / "portfolio.db"

    init_result = runner.invoke(
        app,
        [
            "init-data",
            "--database-path",
            str(database_path),
            "--seed",
            "42",
        ],
    )

    assert init_result.exit_code == 0
    assert database_path.exists()

    result = runner.invoke(
        app,
        [
            "loss-ratio",
            "--database-path",
            str(database_path),
            "--year",
            "2023",
            "--year",
            "2024",
            "--year",
            "2025",
            "--province",
            "QC",
        ],
    )

    assert result.exit_code == 0

    payload = json.loads(result.stdout)

    assert payload["question"]
    assert payload["raw_results"]
    assert payload["answer"]
    assert payload["chart"] is not None
    assert payload["audit"] is not None

    assert payload["tool_calls"] == [
        {
            "tool_name": "get_loss_ratio_by_segment",
            "validated_arguments": {
                "underwriting_years": [2023, 2024, 2025],
                "dimensions": [
                    "province",
                    "line_of_business",
                    "underwriting_year",
                ],
                "provinces": ["QC"],
                "lines_of_business": None,
            },
            "execution_status": "success",
        }
    ]

    assert payload["audit"]["dataset_version"] == "synthetic-v1"
    assert (
        payload["audit"]["calculation_definition"]
        == "paid_loss_ratio = paid_claim_amount / written_premium"
    )

    assert all(row["province"] == "QC" for row in payload["raw_results"])
    assert all(row["written_premium"] > 0 for row in payload["raw_results"])
    assert all(row["paid_claim_amount"] >= 0 for row in payload["raw_results"])
    assert all(row["loss_ratio"] >= 0 for row in payload["raw_results"])


def test_loss_ratio_fails_when_database_does_not_exist(tmp_path: Path) -> None:
    database_path = tmp_path / "missing.db"

    result = runner.invoke(
        app,
        [
            "loss-ratio",
            "--database-path",
            str(database_path),
            "--year",
            "2025",
        ],
    )

    assert result.exit_code != 0
    assert "Database does not exist" in result.stderr
