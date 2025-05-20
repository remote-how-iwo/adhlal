"""Fan-out concurrent LLM calls for the whole batch, using dynamic models."""
from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Type

import pandas as pd
from pydantic import BaseModel

from .generic_analysis import analyse_chat_dynamically # Changed import
# StudentProfile is no longer directly used here, replaced by DynamicModel
from .constants import MAX_CONCURRENT_REQUESTS

_SEM = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def transform_batch_dynamically(
    df: pd.DataFrame,
    config: Dict[str, Any],
    DynamicModel: Type[BaseModel]
) -> List[BaseModel]: # Return type is now List[BaseModel]
    """Fan-out concurrent LLM calls for the whole batch, limited by a semaphore.
    Uses dynamic configuration and model for analysis.
    """
    async def _run(group: pd.DataFrame) -> BaseModel: # Return type is BaseModel
        async with _SEM:
            # Call the new dynamic analysis function
            return await analyse_chat_dynamically(group, config, DynamicModel)

    tasks = [_run(group) for _, group in df.groupby("chat_id")]
    return await asyncio.gather(*tasks) 