"""Turn one chat's participant messages → StudentProfile."""
from __future__ import annotations

import textwrap
import pandas as pd
import json

from .models import StudentProfile
from .openai_utils import call_llm
from .constants import MAX_CORPUS_CHARS

_SCHEMA_EXAMPLE = '''
{{
  "chat_id": 1234,
  "user_email": "user@example.com",
  "consent": true,
  "motivation": "string or null",
  "experience": "string or null",
  "program_choice_reason": "string or null",
  "satisfaction_rating": 4,
  "satisfaction_reason": "string or null",
  "skills_development": "string or null",
  "industry_alignment_rating": 3,
  "industry_alignment_details": "string or null",
  "orientation_interest": true,
  "education": {{
    "institution": "string or null",
    "major": "string or null",
    "graduation_year": 2025
  }},
  "contact_info": {{
    "phone": "string or null",
    "email": "user@example.com"
  }},
  "extracted_at": "2024-05-05T12:00:00Z"
}}
'''

_TEMPLATE = textwrap.dedent(
    f"""
    Chat id: {{chat_id}}
    User email: {{user_email}}

    The following is a concatenation of all *participant* messages (exclude the agent
    questions). Use it to fill every field you can. If a field is truly unknown set it
    to null.

    ===== BEGIN MESSAGES =====
    {{corpus}}
    ===== END  MESSAGES =====

    Output **only** a JSON object strictly matching the following schema (field names and types must match exactly):
    {_SCHEMA_EXAMPLE}
    """
)


def _coerce_llm_output(raw_json: str) -> dict:
    """Post-process LLM output to coerce/rename fields to match StudentProfile schema."""
    data = json.loads(raw_json)
    # Rename 'email' to 'user_email' if present at top level
    if 'email' in data and 'user_email' not in data:
        data['user_email'] = data.pop('email')
    # Coerce education to dict if it's a list
    if isinstance(data.get('education'), list) and data['education']:
        data['education'] = data['education'][0]
    # Coerce contact_info to dict if it's a list
    if isinstance(data.get('contact_info'), list) and data['contact_info']:
        data['contact_info'] = data['contact_info'][0]
    # Coerce ratings (satisfaction_rating, industry_alignment_rating) to nearest integer
    for key in ('satisfaction_rating', 'industry_alignment_rating'):
        val = data.get(key)
        if val is not None:
            try:
                # convert numeric strings or numbers to float
                num = float(val)
                data[key] = int(round(num))
            except (ValueError, TypeError):
                # leave as-is if not numeric
                pass
    # Coerce graduation_year to int if numeric (inside education)
    edu = data.get('education')
    if isinstance(edu, dict):
        gy = edu.get('graduation_year')
        if gy is not None:
            try:
                edu['graduation_year'] = int(round(float(gy)))
            except (ValueError, TypeError):
                pass
    # Convert empty strings to None for cleaner CSV output
    def _blank_to_none(x):
        if isinstance(x, str) and not x.strip():
            return None
        return x
    data = {k: _blank_to_none(v) for k, v in data.items()}
    if 'education' in data and isinstance(data['education'], dict):
        data['education'] = {k: _blank_to_none(v) for k, v in data['education'].items()}
    if 'contact_info' in data and isinstance(data['contact_info'], dict):
        data['contact_info'] = {k: _blank_to_none(v) for k, v in data['contact_info'].items()}
    return data


async def analyse_chat(chat_df: pd.DataFrame) -> StudentProfile:  # noqa: ANN001
    corpus = "\n".join(
        chat_df.loc[chat_df["speaker"] == "participant", "message"].tolist()
    )
    # Truncate corpus if too long to avoid exceeding model context limits
    if len(corpus) > MAX_CORPUS_CHARS:
        corpus = corpus[-MAX_CORPUS_CHARS:]
    prompt = _TEMPLATE.format(
        chat_id=int(chat_df.iloc[0]["chat_id"]),
        user_email=chat_df.iloc[0]["user_email"],
        corpus=corpus,
    )
    # Call LLM and post-process output
    raw_response = call_llm(prompt, str)  # get raw JSON string
    data = _coerce_llm_output(raw_response)
    return StudentProfile.model_validate(data) 