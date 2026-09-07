from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


def get_available_underwriting_years(database_path: Path) -> list[int]:
    """Return all available underwriting years in ascending order."""
    if not database_path.exists():
        raise FileNotFoundError(f"Database does not exist: {database_path}")

    with closing(sqlite3.connect(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT underwriting_year
            FROM policies
            ORDER BY underwriting_year
            """
        ).fetchall()

    return [row[0] for row in rows]
