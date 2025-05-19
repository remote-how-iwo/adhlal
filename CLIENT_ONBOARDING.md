# Adhlal ETL – Client On-Boarding Guide

_Updated: May 2025_

## 1. What problem does this solve?

You have exported thousands of chat conversations from the **AI-Mentor** platform.  Hidden inside every chat are valuable signals about students' motivation, experience, and satisfaction.

The **Adhlal ETL** pipeline turns those raw CSV exports into a **clean, structured database** (or CSV file) that you can slice & dice in Excel, Power BI or any BI tool you like.

* ETL = **E**xtract → **T**ransform → **L**oad.
* "Transform" is powered by OpenAI.  The model reads each student's answers and fills in a validated JSON schema.
* "Load" writes everything into a Postgres table called `student_feedback` (or, if you prefer, into a new CSV file).

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
   git clone https://github.com/adhlal/etl.git
   cd etl
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

### Basic (writes to Postgres)
```bash
poetry run adhlal-etl path/to/chats_export.csv
```

### Advanced (generate a new structured CSV instead of touching the database)
```bash
poetry run adhlal-etl path/to/chats_export.csv \
                      --output-csv structured_output.csv
```

💡 _Tip_: You can open the generated CSV directly in Excel to inspect results.

---

## 4. Frequently asked questions

**Q: How big can the input file be?**  
The current OpenAI context limit is ~128 k tokens.  The code smartly truncates very long chats, so you can safely process thousands of rows.  Typical runtime: ~30 s per 100 chats.

**Q: How much will I pay OpenAI?**  
Each chat triggers one model call.  For `gpt-4o-mini` the cost is ~USD 0.006 per call.  1 000 chats ≈ USD 6.

**Q: Is my data secure?**  
• The pipeline never stores your OpenAI key in the codebase – it lives only in your local `.env` file.  
• All PII stays on your machine and in your database; nothing is logged publicly.

**Q: Can I run it on Windows?**  
Yes.  The helper `windows_loop.py` patches a known asyncio issue so the same command works on Windows PowerShell / CMD.

---

## 5. Under the hood (for the curious)

1. **Extract** – `etl/extract.py` normalises the CSV into tidy columns and converts timestamps.
2. **Transform** – `etl/student_analysis.py` prompts OpenAI with the student's answers and validates the output against a strict Pydantic schema (`etl/models.py`).
3. **Load** – `etl/load.py` upserts each JSON payload into the `student_feedback` table.

Everything is type-checked, retried on network errors, and capped at `MAX_CONCURRENT_REQUESTS` to respect API rate-limits.

---

## 6. Next steps on the live call

1. **Share screen** and walk through this guide.
2. **Clone the repo together** and confirm Python + Poetry install.
3. **Paste their real OpenAI key** into `.env`.
4. **Run a small sample file live** (`sample_data/ten_chats.csv`) so they see results instantly.
5. **Open Postgres / Excel** to explore the structured data.
6. **Explain cost & runtime** expectations.
7. **Hand over ownership** – remind them that from now on the whole process is _one command_.

---

## 7. Support

If you hit any issues:
* open an issue on GitHub
* or email `data-team@adhlal.org` (average reply < 24 h)

Happy analysing! 🎉 