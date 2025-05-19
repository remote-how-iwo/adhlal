"""Thin wrapper around OpenAI with JSON validation + retries."""
from __future__ import annotations

import json
from typing import Type, TypeVar

import openai
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_random_exponential

from .constants import MAX_RETRIES, OPENAI_MODEL, TEMPERATURE

T = TypeVar("T", bound=BaseModel)


@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_random_exponential())
def call_llm(prompt: str, schema: Type | str) -> T | str:
    """Call LLM and coerce strict JSON into `schema`. Raises on failure. If schema is str, return raw JSON string."""

    response = openai.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a strict JSON generator."},
            {"role": "user", "content": prompt},
        ],
    )

    content = response.choices[0].message.content  # pyright: ignore
    if schema is str:
        return content
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as err:
        raise ValueError(f"LLM returned invalid JSON: {content}") from err

    try:
        return schema.model_validate(payload)
    except ValidationError as err:
        raise ValueError(f"LLM JSON does not match schema: {err}") from err 