from __future__ import annotations

from pathlib import Path

import pytest

from insurance_data_analyst_agent.database import (
    get_available_underwriting_years,
)
from insurance_data_analyst_agent.synthetic_data.generator import (
    create_synthetic_database,
)


def test_get_available_underwriting_years_returns_sorted_years(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "portfolio.db"

    create_synthetic_database(
        database_path=database_path,
        seed=42,
    )

    years = get_available_underwriting_years(database_path)

    assert years == [2023, 2024, 2025]


def test_get_available_underwriting_years_rejects_missing_database(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "missing.db"

    with pytest.raises(
        FileNotFoundError,
        match="Database does not exist",
    ):
        get_available_underwriting_years(database_path)
