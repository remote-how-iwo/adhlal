"""Read raw CSV export from AI-Mentor and normalise columns."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

EXPECTED_COLS = {
    "chat_id",
    "user_email",
    "message_author",
    "message_content",
    "message_timestamp",
}


def load_chats(csv_path: str | Path) -> pd.DataFrame:  # noqa: ANN001 – pandas dance
    df = pd.read_csv(csv_path)

    missing = EXPECTED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {', '.join(missing)}")

    # ── standardise shape
    df = df.rename(
        columns={
            "message_content": "message",
            "message_timestamp": "timestamp",
        }
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    df["speaker"] = df["message_author"].str.upper().map(
        lambda role: "participant" if role == "HUMAN" else "agent"
    )

    df = (
        df[[
            "chat_id",
            "user_email",
            "speaker",
            "message",
            "timestamp",
        ]]
        .sort_values(["chat_id", "timestamp"])
        .reset_index(drop=True)
    )

    return df 