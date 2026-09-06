from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from insurance_data_analyst_agent.config import settings
from insurance_data_analyst_agent.models.analytics import (
    Dimension,
    LossRatioRequest,
)
from insurance_data_analyst_agent.services.response_builder import (
    build_loss_ratio_response,
)
from insurance_data_analyst_agent.synthetic_data.generator import (
    create_synthetic_database,
)
from insurance_data_analyst_agent.tools.loss_ratio import (
    get_loss_ratio_by_segment,
)

app = typer.Typer(
    name="insurance-data-analyst",
    help="Controlled and auditable insurance portfolio analytics.",
    no_args_is_help=True,
)

DatabasePathOption = Annotated[
    Path,
    typer.Option(
        "--database-path",
        "-d",
        help="Path to the SQLite portfolio database.",
    ),
]

SeedOption = Annotated[
    int,
    typer.Option(
        "--seed",
        help="Deterministic seed used to generate synthetic data.",
    ),
]

YearOption = Annotated[
    list[int],
    typer.Option(
        "--year",
        "-y",
        help="Underwriting year. Repeat the option for multiple years.",
    ),
]

ProvinceOption = Annotated[
    list[str] | None,
    typer.Option(
        "--province",
        help="Province filter. Repeat the option for multiple provinces.",
    ),
]

LineOfBusinessOption = Annotated[
    list[str] | None,
    typer.Option(
        "--line-of-business",
        "--lob",
        help="Line-of-business filter. Repeat the option for multiple values.",
    ),
]


@app.command("init-data")
def init_data(
    database_path: DatabasePathOption = settings.database_path,
    seed: SeedOption = 20260904,
) -> None:
    """Create the deterministic synthetic insurance portfolio database."""
    create_synthetic_database(
        database_path=database_path,
        seed=seed,
    )

    typer.echo(
        json.dumps(
            {
                "status": "success",
                "database_path": str(database_path),
                "seed": seed,
                "dataset_version": settings.dataset_version,
            },
            indent=2,
        )
    )


@app.command("loss-ratio")
def loss_ratio(
    years: YearOption = ...,
    province: ProvinceOption = None,
    line_of_business: LineOfBusinessOption = None,
    database_path: DatabasePathOption = settings.database_path,
) -> None:
    """Calculate paid loss ratio by province, line of business, and year."""
    if not database_path.exists():
        raise typer.BadParameter(
            f"Database does not exist: {database_path}. Run 'init-data' first."
        )

    request = LossRatioRequest(
        underwriting_years=years,
        dimensions=[
            Dimension.PROVINCE,
            Dimension.LINE_OF_BUSINESS,
            Dimension.UNDERWRITING_YEAR,
        ],
        provinces=province,
        lines_of_business=line_of_business,
    )

    raw_results = get_loss_ratio_by_segment(
        database_path=database_path,
        request=request,
    )

    question = (
        "Show the paid loss ratio by province and line of business "
        f"for underwriting years {', '.join(str(year) for year in years)}."
    )

    response = build_loss_ratio_response(
        question=question,
        request=request,
        raw_results=raw_results,
        database_path=database_path,
        dataset_version=settings.dataset_version,
    )

    typer.echo(response.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
