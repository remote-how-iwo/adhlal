"""Upsert JSONB payloads → Postgres."""
from __future__ import annotations

import json
import os
from typing import Sequence

import psycopg2
from psycopg2.extras import Json, execute_values
from dotenv import load_dotenv

from .models import StudentProfile

load_dotenv()

TABLE = "student_feedback"
DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    chat_id BIGINT PRIMARY KEY,
    payload JSONB NOT NULL,
    extracted_at TIMESTAMP WITH TIME ZONE NOT NULL
);
"""


def _ensure_table(cur):
    cur.execute(DDL)


def load_batch(batch: Sequence[StudentProfile]):
    DSN = os.environ["DATABASE_URL"]
    records = [
        (
            p.chat_id,
            Json(json.loads(p.model_dump_json(exclude_none=True))),
            p.extracted_at,
        )
        for p in batch
    ]

    with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
        _ensure_table(cur)
        execute_values(
            cur,
            f"""
            INSERT INTO {TABLE} (chat_id, payload, extracted_at)
            VALUES %s
            ON CONFLICT (chat_id) DO UPDATE
            SET payload = EXCLUDED.payload,
                extracted_at = EXCLUDED.extracted_at;
            """,
            records,
        ) 