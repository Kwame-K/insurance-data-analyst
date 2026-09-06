from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from insurance_data_analyst_agent.models.analytics import LossRatioRequest

ALLOWED_DIMENSIONS = {
    "province": "p.province",
    "line_of_business": "p.line_of_business",
    "underwriting_year": "p.underwriting_year",
}


def get_loss_ratio_by_segment(
    database_path: Path,
    request: LossRatioRequest,
) -> list[dict[str, Any]]:
    selected_dimensions = [dimension.value for dimension in request.dimensions]

    group_columns = [ALLOWED_DIMENSIONS[dimension] for dimension in selected_dimensions]
    select_dimensions = [
        f"{column} AS {dimension}"
        for dimension, column in zip(selected_dimensions, group_columns, strict=True)
    ]

    year_placeholders = ", ".join("?" for _ in request.underwriting_years)

    where_clauses = [
        f"p.underwriting_year IN ({year_placeholders})",
    ]
    parameters: list[Any] = list(request.underwriting_years)

    if request.provinces:
        province_placeholders = ", ".join("?" for _ in request.provinces)
        where_clauses.append(f"p.province IN ({province_placeholders})")
        parameters.extend(request.provinces)

    if request.lines_of_business:
        lob_placeholders = ", ".join("?" for _ in request.lines_of_business)
        where_clauses.append(f"p.line_of_business IN ({lob_placeholders})")
        parameters.extend(request.lines_of_business)

    select_clause = ", ".join(select_dimensions)
    group_by_clause = ", ".join(group_columns)
    where_clause = " AND ".join(where_clauses)

    query = f"""
        WITH claims_by_policy AS (
            SELECT
                policy_id,
                SUM(paid_amount) AS paid_claim_amount
            FROM claims
            GROUP BY policy_id
        )
        SELECT
            {select_clause},
            ROUND(SUM(p.written_premium), 2) AS written_premium,
            ROUND(COALESCE(SUM(cbp.paid_claim_amount), 0), 2) AS paid_claim_amount,
            ROUND(
                COALESCE(SUM(cbp.paid_claim_amount), 0)
                / NULLIF(SUM(p.written_premium), 0),
                6
            ) AS loss_ratio
        FROM policies AS p
        LEFT JOIN claims_by_policy AS cbp
            ON p.policy_id = cbp.policy_id
        WHERE {where_clause}
        GROUP BY {group_by_clause}
        ORDER BY {group_by_clause}
    """

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]
