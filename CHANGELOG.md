# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - YYYY-MM-DD
### Added
- **Config-driven ETL**: The pipeline can now process different survey types based on YAML configuration files. This allows adding new surveys (e.g., Employer Survey) without Python code changes.
  - New `src/etl/configs/` directory for YAML configurations (`student.yml`, `employer.yml`).
  - `CONFIG_SPEC.md` defining the YAML structure.
  - `src/etl/schema_factory.py` for dynamically generating Pydantic models from configs.
  - `src/etl/generic_analysis.py` for LLM interaction based on dynamic schemas.
  - `src/etl/transform_generic.py` for batch processing with dynamic models.
- CLI updated with a `--config` argument to specify the survey configuration file. Defaults to `student.yml` for backward compatibility.
- `README.md` updated with instructions for the new config-driven approach and how to add new survey types.

### Changed
- Refactored `src/etl/__init__.py` to use the new dynamic config and model loading mechanism.
- `_batch_to_csv` function is now `_batch_to_csv_dynamically` and uses `csv_mapping` from the config.
- `src/etl/student_analysis.py` and `src/etl/transform.py` were replaced by their generic, config-driven counterparts (`generic_analysis.py` and `transform_generic.py`).

### Removed
- Hardcoded student-specific schema and prompt logic from the core ETL pipeline.

## [0.1.0] - PreviousDate
- Initial release of the Adhlal ETL pipeline for student feedback.
  - Extracts data from AI-Mentor CSVs.
  - Transforms data using OpenAI and a Pydantic model (`StudentProfile`).
  - Loads data to PostgreSQL or a structured CSV file. 