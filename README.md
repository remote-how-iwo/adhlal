# Adhlal ETL Pipeline

This project extracts data from AI-Mentor chat exports, transforms it using an LLM
to a structured format based on a configurable survey type, and loads it into a
PostgreSQL database or a CSV file.

## Features

- Processes chat exports from AI-Mentor (CSV format).
- Uses OpenAI's GPT models for structured data extraction.
- Configurable ETL pipeline: easily add new survey types (e.g., student feedback, employer surveys) by defining a YAML configuration file.
- Outputs to PostgreSQL or a structured CSV file.
- Asynchronous processing for improved performance.

## Prerequisites

- Python 3.9+ (project is configured for ^3.11)
- Poetry for dependency management (https://python-poetry.org/)
- OpenAI API Key (set as `OPENAI_API_KEY` environment variable)
- For database output: PostgreSQL connection string (set as `DATABASE_URL` environment variable)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

3.  **Set up environment variables:**
    Copy `env.example` to `.env` and fill in your details:
    ```bash
    cp env.example .env
    # Edit .env with your OPENAI_API_KEY and DATABASE_URL (if using DB output)
    ```
    Supported environment variables (see `src/etl/constants.py` and `.env.example`):
    - `OPENAI_API_KEY`: Your OpenAI API key.
    - `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://user:pass@host:port/dbname`).
    - `OPENAI_MODEL`: (Optional) OpenAI model to use (default: `gpt-4o-mini`).
    - `MAX_CONCURRENT_REQUESTS`: (Optional) Max concurrent calls to OpenAI (default: 10, as per constants.py).
    - `MAX_CORPUS_CHARS`: (Optional) Max characters from chat corpus to send to LLM (default: 20000, as per constants.py).
    - `REQUEST_TIMEOUT_SECONDS`: (Optional) Timeout for OpenAI API requests (default: 120, as per constants.py).

## Running the ETL

The ETL is run from the command line using the `adhlal-etl` script.

**General Syntax:**

```bash
poetry run adhlal-etl <input_csv_path> [--config <config_yaml_path>] [--output-csv <output_csv_path>]
```

-   `<input_csv_path>`: Path to the raw chat export CSV file.
-   `--config <config_yaml_path>`: (Optional) Path to the YAML configuration file for the specific survey type.
    If omitted, it defaults to `src/etl/configs/student.yml` (for the student survey).
    See `src/etl/configs/CONFIG_SPEC.md` for details on the config file format.
-   `--output-csv <output_csv_path>`: (Optional) Path to save the structured output as a CSV file.
    If omitted, the pipeline will attempt to load the data into the PostgreSQL database specified by `DATABASE_URL`.

**Examples:**

1.  **Run Student Survey ETL (default config) and output to CSV:**
    ```bash
    poetry run adhlal-etl path/to/your/Adhlal_all_students.csv --output-csv path/to/output/student_structured_data.csv
    ```

2.  **Run Employer Survey ETL (using employer config) and output to CSV:**
    ```bash
    poetry run adhlal-etl path/to/your/Ahdlal_employers_all.csv --config src/etl/configs/employer.yml --output-csv path/to/output/employer_structured_data.csv
    ```

3.  **Run Student Survey ETL and load to PostgreSQL database (ensure `DATABASE_URL` is set):**
    ```bash
    poetry run adhlal-etl path/to/your/Adhlal_all_students.csv
    ```

## Adding a New Survey Type

To process a new type of survey (e.g., "Mentor Feedback"):

1.  **Create a new YAML configuration file** in the `src/etl/configs/` directory (e.g., `src/etl/configs/mentor_feedback.yml`).
    -   You can copy an existing file like `src/etl/configs/student.yml` or `src/etl/configs/employer.yml` as a template.
    -   Define the `model_name` (Pydantic model name), `schema` (fields and their types to be extracted), `prompt_template` (instructions for the LLM), and `csv_mapping` (how model fields map to CSV columns).
    -   Refer to `src/etl/configs/CONFIG_SPEC.md` for detailed specifications of the configuration file format.

2.  **Run the ETL** pointing to your new configuration file:
    ```bash
    poetry run adhlal-etl path/to/your/new_survey_data.csv --config src/etl/configs/your_new_config.yml --output-csv path/to/output/your_new_structured_data.csv
    ```

No Python code changes are required to add or run new survey types once the configuration file is defined.

## Development

(Information about running tests, linters, etc. would go here if tests were implemented in T-9)

## Project Structure

```
src/
└── etl/
    ├── configs/                # YAML configurations for different survey types
    │   ├── student.yml
    │   ├── employer.yml
    │   └── CONFIG_SPEC.md      # Specification for config files
    ├── samples/                # Sample input and expected output CSV files
    │   ├── student_small.csv
    │   ├── employer_small.csv
    │   └── _expected/
    │       ├── student_small_output.csv
    │       └── employer_small_output.csv
    ├── helpers/
    │   └── windows_loop.py
    ├── __init__.py             # Main ETL package entry point (main, run functions)
    ├── __main__.py             # CLI entry point (defines adhlal-etl script)
    ├── constants.py            # Global constants (OpenAI model, retry limits, etc.)
    ├── extract.py              # Loads and preprocesses raw CSV data
    ├── generic_analysis.py     # Dynamically analyzes chat based on config (LLM interaction)
    ├── load.py                 # Loads structured data into PostgreSQL
    ├── models.py               # Original Pydantic models (Likert, common types), now mostly for reference or shared types
    ├── openai_utils.py         # Utilities for OpenAI API calls
    ├── schema_factory.py       # Dynamically creates Pydantic models from YAML configs
    └── transform_generic.py    # Orchestrates the transformation batch processing (replaces transform.py)

.env.example                    # Example environment variables file
CHANGELOG.md                    # Tracks changes across versions
poetry.lock
README.md
```

> 👉 New here?  **Jump straight to the [Client On-Boarding Guide](CLIENT_ONBOARDING.md)** – a step-by-step walkthrough for non-technical stakeholders.

---

## Quick-start (developers)
```bash
# 1. Install dependencies in an isolated env
poetry install               

# 2. Create your env vars
cp env.example .env   # then edit it to add secrets

# 3. Run the pipeline
poetry run adhlal-etl path/to/chats.csv
```

### CSV-only mode (no database)
```bash
poetry run adhlal-etl path/to/chats.csv --output-csv structured_output.csv
```

---

## Environment variables
| key              | description                               |
| ---------------- | ----------------------------------------- |
| `OPENAI_API_KEY` | OpenAI secret (never commit this!)        |
| `OPENAI_MODEL`   | Defaults to `gpt-4o-mini` if unset        |
| `DATABASE_URL`   | `postgres://user:pass@host:5432/database` |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent calls to OpenAI (default: 10) |
| `MAX_CORPUS_CHARS` | Max chat characters for LLM context (default: 20000) |
| `REQUEST_TIMEOUT_SECONDS` | OpenAI API request timeout (default: 120) |

See `src/etl/schema_factory.py` (for dynamically generated models) and `src/etl/configs/*.yml` for the schemas that define the structure stored in Postgres or CSV.
The original `src/etl/models.py` now primarily contains shared Pydantic types like `Likert`. 