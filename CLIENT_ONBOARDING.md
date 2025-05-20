# Adhlal ETL – Client On-Boarding Guide

_Updated: May 2025_

## 1. What problem does this solve?

You have exported thousands of chat conversations from the **AI-Mentor** platform. Hidden inside every chat are valuable signals about your users' (e.g., students, employers) motivation, experience, and satisfaction.

The **Adhlal ETL** pipeline turns those raw CSV exports into a **clean, structured database** (or CSV file) that you can slice & dice in Excel, Power BI or any BI tool you like.

* ETL = **E**xtract → **T**ransform → **L**oad.
* "Transform" is powered by OpenAI. The model reads each user's answers and fills in a validated JSON schema, defined by a survey-specific configuration file.
* "Load" writes everything into a Postgres table (the name can vary based on configuration) or, if you prefer, into a new CSV file.

---

## 2. One-time set-up (10 min)

1. **Install Python 3.11+**
   • Windows 👉 https://www.python.org/downloads/windows/  
   • macOS 👉 `brew install python@3.11`
2. **Install Poetry** (our dependency manager)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. **Clone the repository**
   ```bash
   git clone https://github.com/remote-how-iwo/adhlal.git
   cd adhlal
   ```
4. **Install dependencies** (runs in an isolated virtual-env)
   ```bash
   poetry install --without dev
   ```
5. **Create your `.env` file**
   ```bash
   cp env.example .env
   # then open .env in any text editor and paste:
   #  • your OpenAI key
   #  • your Postgres `DATABASE_URL` (skip this if you only want CSV output)
   ```

That's it! 🚀  From now on every command is run via `poetry run …` which guarantees the correct Python version & libraries.

---

## 3. Running the pipeline

The main command is `poetry run adhlal-etl <input_csv_path> [options]`.

### For the Student Survey (default)

**Option 1: Generate a new structured CSV**
```bash
poetry run adhlal-etl path/to/your/student_chats_export.csv --output-csv path/to/output/student_structured_data.csv
```

**Option B: Write to Postgres** (ensure `DATABASE_URL` is set in your `.env` file)

```bash
poetry run adhlal-etl path/to/your/student_chats_export.csv
```
This uses the default configuration found at `src/etl/configs/student.yml`.

### For Other Survey Types (e.g., Employer Survey)

You **must** specify the configuration file for other survey types using the `--config` flag.

**Example: Employer Survey, output to CSV**
```bash
poetry run adhlal-etl path/to/your/employer_chats_export.csv --config src/etl/configs/employer.yml --output-csv path/to/output/employer_structured_data.csv
```

**Example: Employer Survey, output to Postgres** (ensure `DATABASE_URL` is set)
```bash
poetry run adhlal-etl path/to/your/employer_chats_export.csv --config src/etl/configs/employer.yml
```

To add a new survey type (e.g., "Mentor Feedback"), you or your technical team would create a new YAML configuration file in `src/etl/configs/`. See the main `README.md` for technical details on creating these configuration files.

💡 _Tip_: You can open the generated CSV directly in Google Sheets/Excel to inspect results.

---

## 4. Frequently asked questions

**Q: How big can the input file be?**  
The current OpenAI context limit is ~128 k tokens.  The code smartly truncates very long chats, so you can safely process thousands of rows.  Typical runtime: ~30 s per 100 chats.

**Q: How much will I pay OpenAI?**  
Check API pricing: https://openai.com/api/pricing/

**Q: Is my data secure?**  
• The pipeline never stores your OpenAI key in the codebase – it lives only in your local `.env` file.  

**Q: Can I run it on Windows?**  
Yes.  The helper `windows_loop.py` patches a known asyncio issue so the same command works on Windows PowerShell / CMD.

---

## 5. Under the hood (for the curious)

1. **Extract** – `etl/extract.py` normalises the raw input CSV into tidy columns and converts timestamps.
2. **Transform** – `etl/generic_analysis.py` reads the specified YAML configuration (e.g., from `src/etl/configs/student.yml` or `src/etl/configs/employer.yml`). This configuration defines the data schema and the prompt for OpenAI. `etl/schema_factory.py` dynamically creates the data model based on this schema. Then, `generic_analysis.py` prompts OpenAI with the user's answers and validates the output against this dynamic model.
3. **Load** – `etl/load.py` upserts each structured JSON payload into the relevant Postgres table (if not outputting to CSV).

Everything is type-checked, retried on network errors, and capped at `MAX_CONCURRENT_REQUESTS` to respect API rate-limits.

---

## 6. Next steps on the live call

1. **Share screen** and walk through this guide.
2. **Clone the repo together** and confirm Python + Poetry install.
3. **Paste real OpenAI key** into `.env`.
4. **Run a small sample file live** for a relevant survey type (e.g., `src/etl/samples/student_small.csv` with the student config, or `src/etl/samples/employer_small.csv` with the employer config) so participants can see results instantly.
5. **Open Postgres / Excel** to explore the structured data.
6. **Explain cost & runtime** expectations.
7. **Hand over ownership** – remind them that from now on the whole process is _one command_.

---
