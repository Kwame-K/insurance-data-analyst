# Insurance Data Analyst Agent

A controlled, deterministic, and auditable AI-agent architecture for insurance portfolio analytics.

The project accepts selected analytical questions in natural language, routes each supported request to a pre-defined analytical tool, executes deterministic Python and SQLite calculations, generates optional charts, and persists a complete audit record for every run.

## Project goals

This project demonstrates a safe approach to building an analytical agent for an insurance portfolio.

The agent:

- Accepts supported analytical questions in English and French
- Routes questions to an allow-listed analytical tool
- Validates tool arguments with Pydantic
- Does not generate or execute free-form SQL
- Performs all business calculations in deterministic Python and SQLite code
- Produces structured JSON responses
- Generates optional chart files through Python
- Persists a JSON audit artifact for successful and failed runs
- Uses synthetic insurance data only

## Current V1 capability

The current V1 supports paid loss-ratio analysis by:

- Province
- Line of business
- Underwriting year

Examples of supported questions:

```text
Show the loss ratio by region and line of business for the last three underwriting years.
```

```text
Show the paid loss ratio for commercial property in Quebec for 2025.
```

```text
Afficher le ratio de sinistralité pour la propriété commerciale au Québec pour 2024 et 2025.
```

Examples of intentionally unsupported questions:

```text
What is the average claim severity by province?
```

```text
Flag segments where claim frequency increased by more than 20% year over year.
```

Unsupported questions are rejected explicitly and do not trigger an analytical tool.

## Architecture

```text
User question
    ↓
CLI: insurance-data-analyst ask
    ↓
InsuranceDataAnalystAgent
    ↓
DeterministicRouter
    ↓
ToolSelection validated by Pydantic
    ↓
ToolRegistry
    ↓
get_loss_ratio_by_segment
    ↓
SQLite query and deterministic calculation
    ↓
AnalyticsResponse
    ↓
Optional Matplotlib chart
    ↓
Persistent JSON audit artifact
```

## Safety principles

### No free-form SQL

The user and the routing layer never provide SQL directly to SQLite.

The application uses fixed SQL templates with:

- Allow-listed dimensions
- Parameterized value filters
- Validated underwriting years
- Validated province filters
- Validated line-of-business filters

### Deterministic business calculations

The LLM layer is not responsible for calculations.

Insurance metrics are calculated by explicit Python and SQLite logic. The current V1 defines:

```text
paid_loss_ratio = total_paid_claim_amount / total_written_premium
```

### Full audit trail

Each call to `agent.answer()` produces a JSON audit artifact containing:

- Unique run identifier
- UTC timestamp
- Agent version
- Dataset version
- Database path
- Original user question
- Tool selected
- Validated tool arguments
- Raw analytical results
- Final structured response
- Error details, when execution fails

## Project structure

```text
insurance-data-analyst-agent/
├── data/
│   └── insurance_portfolio.db
├── output/
│   ├── audits/
│   │   └── .gitkeep
│   └── charts/
│       └── .gitkeep
├── src/
│   └── insurance_data_analyst_agent/
│       ├── charts.py
│       ├── cli.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       │   ├── analytics.py
│       │   ├── audit.py
│       │   └── routing.py
│       ├── services/
│       │   ├── agent.py
│       │   ├── audit_writer.py
│       │   ├── response_builder.py
│       │   └── router.py
│       ├── synthetic_data/
│       │   └── generator.py
│       └── tools/
│           ├── loss_ratio.py
│           └── registry.py
├── tests/
│   ├── evaluations/
│   │   ├── cases.json
│   │   └── test_router_evaluations.py
│   ├── test_agent.py
│   ├── test_audit_writer.py
│   ├── test_charts.py
│   ├── test_cli.py
│   ├── test_database.py
│   ├── test_loss_ratio.py
│   ├── test_registry.py
│   └── test_router.py
├── .env.example
├── pyproject.toml
└── README.md
```

## Installation

### Prerequisites

- Python 3.11 or later
- uv
- Git

### Clone and install

```bash
git clone <YOUR_REPOSITORY_URL>
cd insurance-data-analyst-agent
uv sync
```

### Configure environment variables

Create a local environment file:

```bash
cp .env.example .env
```

Default `.env` configuration:

```dotenv
DATABASE_PATH=data/insurance_portfolio.db
AUDIT_DIRECTORY=output/audits
DATASET_VERSION=synthetic-v1
```

The `.env` file must not be committed to Git.

## Quick start

### Create deterministic synthetic data

```bash
uv run insurance-data-analyst init-data
```

Create the database with a specific reproducible seed:

```bash
uv run insurance-data-analyst init-data \
  --seed 42 \
  --database-path data/insurance_portfolio.db
```

### Run direct loss-ratio analysis

```bash
uv run insurance-data-analyst loss-ratio \
  --year 2023 \
  --year 2024 \
  --year 2025
```

Filter by province:

```bash
uv run insurance-data-analyst loss-ratio \
  --year 2025 \
  --province QC
```

Filter by province and line of business:

```bash
uv run insurance-data-analyst loss-ratio \
  --year 2025 \
  --province QC \
  --line-of-business commercial_property
```

### Ask a natural-language question

```bash
uv run insurance-data-analyst ask \
  "Show the paid loss ratio for commercial property in Quebec for 2025."
```

French example:

```bash
uv run insurance-data-analyst ask \
  "Afficher le ratio de sinistralité pour la propriété commerciale au Québec pour 2024 et 2025."
```

### Generate a chart

```bash
uv run insurance-data-analyst ask \
  "Show the loss ratio by region and line of business for the last three underwriting years." \
  --chart-output output/charts/loss-ratio-by-segment.png
```

The command produces:

- A structured JSON response in standard output
- A chart PNG file in `output/charts/`
- A complete audit JSON file in `output/audits/`

## Example response

```json
{
  "question": "Show the paid loss ratio for commercial property in Quebec for 2025.",
  "tool_calls": [
    {
      "tool_name": "get_loss_ratio_by_segment",
      "validated_arguments": {
        "underwriting_years": [2025],
        "dimensions": [
          "province",
          "line_of_business",
          "underwriting_year"
        ],
        "provinces": ["QC"],
        "lines_of_business": ["commercial_property"]
      },
      "execution_status": "success"
    }
  ],
  "raw_results": [
    {
      "province": "QC",
      "line_of_business": "commercial_property",
      "underwriting_year": 2025,
      "written_premium": 0.0,
      "paid_claim_amount": 0.0,
      "loss_ratio": 0.0
    }
  ],
  "answer": "The analysis returned portfolio segments.",
  "chart": {
    "chart_type": "grouped_bar",
    "x": "underwriting_year",
    "y": "loss_ratio",
    "series": [
      "province",
      "line_of_business"
    ],
    "title": "Paid loss ratio by province and line of business",
    "output_path": "output/charts/loss-ratio-by-segment.png"
  },
  "audit": {
    "dataset_version": "synthetic-v1",
    "calculation_definition": "paid_loss_ratio = paid_claim_amount / written_premium",
    "database_path": "data/insurance_portfolio.db"
  }
}
```

The numeric values in the example are illustrative. Actual values depend on the seed used to generate the synthetic dataset.

## Audit artifacts

Audit files are created in:

```text
output/audits/
```

Example file name:

```text
20260907T051500123456Z_550e8400-e29b-41d4-a716-446655440000.json
```

Inspect the latest audit artifact:

```bash
ls -t output/audits/*.json | head -n 1 | xargs cat
```

List generated charts:

```bash
ls -lh output/charts
```

## Testing and quality checks

Run formatting:

```bash
uv run ruff format src tests
```

Check formatting and linting:

```bash
uv run ruff check src tests
```

Run the complete test suite:

```bash
uv run pytest -v
```

Run test coverage:

```bash
uv run pytest \
  --cov=insurance_data_analyst_agent \
  --cov-report=term-missing \
  --cov-report=html
```

Run only router evaluations:

```bash
uv run pytest tests/evaluations -v
```

## Definitions

| Metric | V1 definition |
|---|---|
| Underwriting year | Year in which the policy was written |
| Written premium | Synthetic premium stored in the `policies` table |
| Paid claim amount | Sum of synthetic paid claim amounts linked to policies |
| Paid loss ratio | `paid_claim_amount / written_premium` |
| Exposure | Synthetic exposure records available for future tools |
| Claim frequency | Planned for a future tool |
| Claim severity | Planned for a future tool |

## Known limitations

This is a portfolio and learning project using synthetic data. It is not a production underwriting or actuarial system.

Current limitations:

- Only paid loss ratio is supported in V1
- The metric uses written premium, not earned premium
- Claims include paid amounts only
- Case reserves and incurred losses are not modeled
- Accident year and calendar year views are not implemented
- No development triangles or reserving calculations are included
- The router supports a limited list of English and French expressions
- The dataset includes only a small set of provinces and lines of business
- Only grouped bar charts are generated in V1
- No authentication, authorization, user management, or production database exists
- No real policyholder, claims, broker, or personally identifiable information is used

## Roadmap

### V1.1

- Add `get_claim_frequency_trend`
- Flag segments with year-over-year frequency increases above 20%
- Add `get_exposure_summary`
- Add `get_portfolio_quality_metrics`
- Support line charts in addition to grouped bar charts
- Add a generic response-builder registry

### V2

- Add provider-agnostic `LLMClient`
- Add Groq and Google Gemini adapters
- Require structured LLM tool selection validated by Pydantic
- Keep deterministic routing as fallback
- Add a FastAPI interface
- Add a Streamlit analytics interface
- Add PostgreSQL and Docker support
- Add CI/CD through GitHub Actions
- Add more realistic insurance data-generation assumptions

## License

License to be defined.

## Author

Kwame Kristian Laban  
Data Science and Insurance Analytics Portfolio
