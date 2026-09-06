from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from insurance_data_analyst_agent.models.analytics import (
    Dimension,
    LossRatioRequest,
)
from insurance_data_analyst_agent.synthetic_data.generator import (
    create_synthetic_database,
)
from insurance_data_analyst_agent.tools.loss_ratio import (
    get_loss_ratio_by_segment,
)


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "insurance_portfolio.db"
    create_synthetic_database(path, seed=42, policies_per_segment_year=10)
    return path


def test_loss_ratio_returns_expected_dimensions(database_path: Path) -> None:
    request = LossRatioRequest(
        underwriting_years=[2023, 2024, 2025],
        dimensions=[
            Dimension.PROVINCE,
            Dimension.LINE_OF_BUSINESS,
            Dimension.UNDERWRITING_YEAR,
        ],
    )

    results = get_loss_ratio_by_segment(database_path, request)

    assert results
    assert {
        "province",
        "line_of_business",
        "underwriting_year",
        "written_premium",
        "paid_claim_amount",
        "loss_ratio",
    } == set(results[0])


def test_loss_ratio_is_non_negative(database_path: Path) -> None:
    request = LossRatioRequest(
        underwriting_years=[2025],
        dimensions=[Dimension.PROVINCE],
    )

    results = get_loss_ratio_by_segment(database_path, request)

    assert all(row["written_premium"] > 0 for row in results)
    assert all(row["paid_claim_amount"] >= 0 for row in results)
    assert all(row["loss_ratio"] >= 0 for row in results)


def test_duplicate_years_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        LossRatioRequest(
            underwriting_years=[2025, 2025],
            dimensions=[Dimension.PROVINCE],
        )


def test_loss_ratio_does_not_duplicate_premium_for_multiple_claims(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "multiple_claims.db"

    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE policies (
                policy_id TEXT PRIMARY KEY,
                province TEXT NOT NULL,
                line_of_business TEXT NOT NULL,
                underwriting_year INTEGER NOT NULL,
                written_premium REAL NOT NULL
            );

            CREATE TABLE claims (
                claim_id TEXT PRIMARY KEY,
                policy_id TEXT NOT NULL,
                claim_year INTEGER NOT NULL,
                claim_type TEXT NOT NULL,
                paid_amount REAL NOT NULL
            );
            """
        )

        connection.execute(
            """
            INSERT INTO policies (
                policy_id,
                province,
                line_of_business,
                underwriting_year,
                written_premium
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "P-001",
                "QC",
                "commercial_property",
                2025,
                1_000.00,
            ),
        )

        connection.executemany(
            """
            INSERT INTO claims (
                claim_id,
                policy_id,
                claim_year,
                claim_type,
                paid_amount
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "C-001",
                    "P-001",
                    2025,
                    "property_damage",
                    200.00,
                ),
                (
                    "C-002",
                    "P-001",
                    2025,
                    "property_damage",
                    300.00,
                ),
            ],
        )

    request = LossRatioRequest(
        underwriting_years=[2025],
        dimensions=[
            Dimension.PROVINCE,
            Dimension.LINE_OF_BUSINESS,
            Dimension.UNDERWRITING_YEAR,
        ],
    )

    results = get_loss_ratio_by_segment(
        database_path=database_path,
        request=request,
    )

    assert len(results) == 1

    result = results[0]

    assert result["written_premium"] == 1_000.00
    assert result["paid_claim_amount"] == 500.00
    assert result["loss_ratio"] == 0.5
