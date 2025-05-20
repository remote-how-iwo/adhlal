# ETL Configuration File Specification

This document describes the structure and fields for the YAML configuration files used by the ETL process. Each YAML file defines a specific survey type.

## File Location

Configuration files should be placed in the `src/etl/configs/` directory.

## Top-Level Fields

- `model_name` (string): A descriptive name for the model/survey (e.g., "StudentProfile", "EmployerSurvey"). This is primarily used for logging and identification.
- `schema` (object): Defines the data structure to be extracted by the LLM.
    - Keys are the field names (e.g., `chat_id`, `user_email`, `motivation`).
    - Values are strings representing the Pydantic type for that field.
        - Supported primitive types: `int`, `str`, `bool`, `float`, `datetime`.
        - Pydantic specific types: `EmailStr`, `Likert`.
        - Use `| None` to indicate an optional field (e.g., `"str | None"`).
        - For nested objects (like `education` or `contact_info`), define them as a nested mapping.
- `prompt_template` (string): A multi-line string that serves as the template for the LLM prompt.
    - It should use `{placeholder}` syntax for dynamic values that will be injected at runtime (e.g., `{chat_id}`, `{user_email}`, `{corpus}`, `{_SCHEMA_EXAMPLE}`).
    - `_SCHEMA_EXAMPLE` is a special placeholder that will be automatically populated with a JSON representation of the `schema` defined above.
- `csv_mapping` (object): Defines how the extracted model fields map to CSV column headers.
    - Keys are the desired CSV column header names.
    - Values are strings representing the path to the field in the extracted model (e.g., `"chat_id"`, `"education.institution"`).

## Example (`student.yml` excerpt)

```yaml
model_name: StudentProfile
schema:
  chat_id: int
  user_email: "EmailStr"
  consent: "bool | None"
  education:
    institution: "str | None"
    major: "str | None"
    graduation_year: "int | None"
  # ... more fields

prompt_template: |
  Chat id: {chat_id}
  User email: {user_email}

  The following is a concatenation of all *participant* messages...
  ...
  Output **only** a JSON object strictly matching the following schema (field names and types must match exactly):
  {_SCHEMA_EXAMPLE}

csv_mapping:
  chat_id: "chat_id"
  user_email: "user_email"
  consent: "consent"
  education__institution: "education.institution" # Accessing nested field
  # ... more mappings
``` 