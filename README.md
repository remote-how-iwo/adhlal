# Adhlal ETL – Fashion-skills intelligence

This repository contains a **turn-key ETL pipeline** that transforms raw AI-Mentor chat exports into a clean, analytics-ready dataset.

* **Extract** – reads the CSV export that AI-Mentor gives you.
* **Transform** – uses OpenAI to fill a validated JSON schema for every student.
* **Load** – upserts the data into Postgres _or_ writes a new structured CSV.

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

See `src/etl/models.py` for the JSON schema stored in Postgres. 