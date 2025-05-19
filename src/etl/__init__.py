"""Package entry-points."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional
import pandas as pd

from dotenv import load_dotenv

from .extract import load_chats
from .transform import transform_batch
from .load import load_batch
from .models import StudentProfile

load_dotenv()


def _batch_to_csv(batch, output_csv_path):
    # Convert batch of StudentProfile to DataFrame matching the structured output
    rows = []
    for p in batch:
        row = {
            "chat_id": p.chat_id,
            "user_email": p.user_email,
            "consent": p.consent,
            "motivation": p.motivation,
            "experience": p.experience,
            "program_choice_reason": p.program_choice_reason,
            "satisfaction_rating": p.satisfaction_rating,
            "satisfaction_reason": p.satisfaction_reason,
            "skills_development": p.skills_development,
            "industry_alignment_rating": p.industry_alignment_rating,
            "industry_alignment_details": p.industry_alignment_details,
            "orientation_interest": p.orientation_interest,
            "education__institution": p.education.institution if p.education else None,
            "education__major": p.education.major if p.education else None,
            "education__graduation_year": p.education.graduation_year if p.education else None,
            "contact_info__phone": p.contact_info.phone if p.contact_info else None,
            "contact_info__email": p.contact_info.email if p.contact_info else None,
        }
        # Determine if there is meaningful data beyond chat_id and user_email
        meaningful_keys = [
            k for k in row.keys() if k not in ("chat_id", "user_email")
        ]
        if all(row[k] in (None, "", []) for k in meaningful_keys):
            # Skip rows with no extracted information
            continue
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(output_csv_path, index=False)


async def main(csv_path: str | Path, output_csv_path: Optional[str] = None) -> None:  # noqa: D401 – imperative
    """Run the full ETL for a single CSV file."""
    df = load_chats(csv_path)
    batch = await transform_batch(df)
    if output_csv_path:
        _batch_to_csv(batch, output_csv_path)
    else:
        load_batch(batch)


def run(csv_path: str | Path, output_csv_path: Optional[str] = None):  # noqa: D401 – imperative
    """Sync wrapper for Windows & *nix CLI."""
    asyncio.run(main(csv_path, output_csv_path)) 