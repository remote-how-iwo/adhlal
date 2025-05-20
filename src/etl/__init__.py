"""Package entry-points for the dynamic ETL pipeline."""
from __future__ import annotations

import asyncio
import json # For potential use in load_batch if model_dump_json is not directly used.
from pathlib import Path
from typing import Optional, List, Dict, Any, Type
import pandas as pd
import yaml
from pydantic import BaseModel

from dotenv import load_dotenv

from .extract import load_chats
from .transform_generic import transform_batch_dynamically # Updated import
from .load import load_batch # Assumed compatible
from .schema_factory import load_config_and_create_model # New import for dynamic models
# StudentProfile is no longer imported directly, replaced by DynamicModel

load_dotenv()


def _get_value_from_path(obj: BaseModel, path: str) -> Any:
    """Accesses a value in a Pydantic model using a dot-separated path."""
    parts = path.split('.')
    value = obj
    for part in parts:
        if value is None: # If a parent object in the path is None, return None
            return None
        if isinstance(value, dict):
            value = value.get(part)
        else:
            try:
                value = getattr(value, part)
            except AttributeError:
                return None # Path does not exist
    return value

def _batch_to_csv_dynamically(
    batch: List[BaseModel],
    csv_mapping: Dict[str, str],
    output_csv_path: str | Path
) -> None:
    """Convert a batch of dynamic Pydantic model instances to a CSV file based on csv_mapping."""
    if not batch:
        # Create an empty CSV with headers if the batch is empty
        df = pd.DataFrame(columns=list(csv_mapping.keys()))
        df.to_csv(output_csv_path, index=False)
        return

    rows = []
    for p_instance in batch:
        row = {}
        for csv_header, model_path in csv_mapping.items():
            row[csv_header] = _get_value_from_path(p_instance, model_path)
        
        # Determine if there is meaningful data beyond chat_id and user_email (if they exist)
        # This logic might need to be made more flexible or configurable
        meaningful_keys = [
            k for k in row.keys() if k.lower() not in ("chat_id", "user_email", "extracted_at")
        ]
        if not meaningful_keys or all(row[k] in (None, "", []) for k in meaningful_keys):
             # Skip rows with no extracted information beyond identifiers, unless config says otherwise
             # For now, we keep this logic similar to original for student profiles.
             # A more robust solution might involve a config flag: `skip_empty_extractions: true`
            pass # Potentially skip, or ensure identifiers are still written if that's desired.
            # If we must write something, ensure chat_id and user_email are present if mapped.
            # if "chat_id" not in row and "chat_id" in csv_mapping.values(): # crude check
            # continue # skip empty
        rows.append(row)
    
    if not rows and batch: # All rows were considered empty by the logic above
        # Fallback: create rows with at least the mapped identifiers if available
        # Or write an empty CSV with headers if no identifiers are reliably present or mapped.
        # This ensures we don't write a completely empty file if all data rows are filtered out
        # but there was data in the batch.
        # For now, if all are filtered, an empty df with headers will be written.
        pass 

    df = pd.DataFrame(rows)
    # Ensure all columns from csv_mapping are present, even if all values were None
    for header in csv_mapping.keys():
        if header not in df.columns:
            df[header] = None
    df = df[list(csv_mapping.keys())] # Order columns as per mapping
    df.to_csv(output_csv_path, index=False)


async def main(
    csv_path: str | Path,
    config_path: str | Path = "src/etl/configs/student.yml", # Default to student config
    output_csv_path: Optional[str | Path] = None
) -> None:
    """Run the full ETL for a single CSV file using a dynamic configuration."""
    
    # Load YAML configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create dynamic Pydantic model from schema in config
    DynamicModel: Type[BaseModel] = load_config_and_create_model(str(config_path)) # schema_factory handles this

    df_input = load_chats(csv_path) # Extract remains the same
    
    # Transform using the dynamic model and config
    batch_of_models = await transform_batch_dynamically(df_input, config, DynamicModel)
    
    if output_csv_path:
        csv_mapping = config.get("csv_mapping", {})
        if not csv_mapping:
            print("Warning: No csv_mapping found in config. CSV output will be empty or incomplete.")
        _batch_to_csv_dynamically(batch_of_models, csv_mapping, output_csv_path)
    else:
        # Load to database (assumed compatible with list of Pydantic models)
        # The load_batch function expects StudentProfile, but since it converts to JSON,
        # it should work with any Pydantic model that has chat_id and extracted_at.
        # We might need to ensure these fields are present or handle them in load_batch.
        # For now, let's assume load_batch is flexible or will be updated.
        # The current load_batch extracts p.chat_id, p.model_dump_json, p.extracted_at.
        # So, the DynamicModel MUST have these attributes for load_batch to work.
        # This should be enforced by the schema definition in the YAML for DB loading.
        load_batch(batch_of_models) 


def run( # Sync wrapper
    csv_path: str | Path,
    config_path: str | Path = "src/etl/configs/student.yml",
    output_csv_path: Optional[str | Path] = None
): 
    """Sync wrapper for Windows & *nix CLI."""
    # patch_windows_event_loop() # This should be called in __main__.py if still needed
    asyncio.run(main(csv_path, config_path, output_csv_path)) 