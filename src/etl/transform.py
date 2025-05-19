"""Fan-out concurrent LLM calls for the whole batch."""
from __future__ import annotations

import asyncio
from typing import List

import pandas as pd

from .student_analysis import analyse_chat
from .models import StudentProfile
from .constants import MAX_CONCURRENT_REQUESTS

_SEM = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def transform_batch(df: pd.DataFrame) -> List[StudentProfile]:  # noqa: ANN001
    """Fan-out concurrent LLM calls for the whole batch, limited by a semaphore to avoid API overload."""
    async def _run(group: pd.DataFrame) -> StudentProfile:
        async with _SEM:
            return await analyse_chat(group)

    tasks = [_run(group) for _, group in df.groupby("chat_id")]
    return await asyncio.gather(*tasks) 