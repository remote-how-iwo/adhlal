"""Turn one chat's participant messages into a dynamic Pydantic model instance based on config."""
from __future__ import annotations

import json
import textwrap # Not strictly needed if prompt_template is already dedented in YAML
from typing import Dict, Any, Type, Union, Optional

import pandas as pd
from pydantic import BaseModel

from .openai_utils import call_llm
from .constants import MAX_CORPUS_CHARS # Assuming this is still relevant
from .schema_factory import create_dynamic_model, generate_schema_example
from .models import Likert # Added import for Likert

# Mapping for Likert scale string values to integers
LIKERT_STRING_TO_INT_MAP: Dict[str, int] = {
    # English
    "not satisfied at all": 1,
    "somewhat dissatisfied": 2,
    "very_dissatisfied": 1,
    "disagree": 2,
    "neutral": 3,
    "satisfied": 4,
    "agree": 4,
    "very satisfied": 5,
    "very_satisfied": 5,
    "weak": 2,
    "poor": 2,
    "very_poor": 1,
    "fair": 3,
    "very_good": 5,
    "very_bad": 1,
    # Arabic (common terms based on observations and translations)
    "غير راضٍ على الإطلاق": 1,
    "غير راض": 2, # "Not satisfied" / "Dissatisfied"
    "محايد": 3, # "Neutral"
    "راضٍ": 4, # "Satisfied"
    "راضٍ جدًا": 5, # "Very satisfied"
    "نوعا ما نعم": 4, # "Kind of yes" / "Yes, somewhat" - mapped to 4 as "satisfied"
    "ضعيف": 2, # "Weak" / "Poor" - mapped to 2
    # Numerical strings
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
}

def _coerce_llm_output(raw_json: str, DynamicModel: Type[BaseModel]) -> dict:
    """Post-process LLM output to coerce/rename fields to match the dynamic schema.
       This version includes specific handling for Likert scale string-to-int conversion.
    """
    data = json.loads(raw_json)
    coerced_data = {}

    # Example coercions (can be expanded or made config-driven if needed):
    if 'email' in data and 'user_email' not in data and hasattr(DynamicModel, 'user_email'):
        data['user_email'] = data.pop('email')
    
    # Convert empty strings to None for cleaner CSV output (apply generally)
    # This function is now applied after specific coercions like Likert.
    def _blank_to_none(x, field_info=None):
        if isinstance(x, str) and not x.strip():
            return None
        if isinstance(x, dict) and field_info and hasattr(field_info.annotation, 'model_fields'):
            nested_model_fields = field_info.annotation.model_fields
            return {k_n: _blank_to_none(v_n, nested_model_fields.get(k_n)) for k_n, v_n in x.items()}
        return x

    for key, value in data.items():
        if key in DynamicModel.model_fields:
            field_info = DynamicModel.model_fields[key]
            current_value = value # Original value from LLM for this key

            # Check if the field is a Likert scale type
            actual_type = field_info.annotation
            is_optional_likert = False
            is_direct_likert = actual_type == Likert

            if getattr(actual_type, '__origin__', None) is Union: # Handles Optional[Likert]
                type_args = getattr(actual_type, '__args__', ())
                if Likert in type_args and type(None) in type_args:
                    is_optional_likert = True
            
            is_likert_field = is_direct_likert or is_optional_likert

            if is_likert_field:
                processed_likert = False
                if isinstance(current_value, str):
                    normalized_value = current_value.strip().lower()
                    mapped_value = LIKERT_STRING_TO_INT_MAP.get(normalized_value)
                    if mapped_value is not None:
                        coerced_data[key] = mapped_value
                        processed_likert = True
                    else:
                        try:
                            num_val_float = float(current_value)
                            num_val_int = int(round(num_val_float))
                            if 1 <= num_val_int <= 5:
                                coerced_data[key] = num_val_int
                                processed_likert = True
                            # else: Let Pydantic validate if out of Likert enum range (if not caught by map/direct conversion)
                        except ValueError:
                            pass # Not a simple number string, will be handled by _blank_to_none or Pydantic
                elif isinstance(current_value, (int, float)):
                    try:
                        num_val = int(round(float(current_value)))
                        if 1 <= num_val <= 5:
                           coerced_data[key] = num_val
                           processed_likert = True
                        # else: let Pydantic handle out-of-range numbers
                    except (ValueError, TypeError):
                        pass # Will be handled by _blank_to_none or Pydantic
                
                if not processed_likert: # If not processed as Likert, store original (or blank_to_none version)
                    coerced_data[key] = _blank_to_none(current_value, field_info)
            
            elif key == "education" and isinstance(current_value, dict) and "graduation_year" in current_value:
                # Handle graduation_year specifically within the education block if education itself is being processed
                edu_data_copy = current_value.copy() # Operate on a copy
                grad_year = edu_data_copy.get("graduation_year")
                if grad_year is not None:
                    try:
                        year_str = str(grad_year)
                        # Convert Eastern Arabic numerals to Western
                        eastern_to_western_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
                        western_year_str = year_str.translate(eastern_to_western_map)
                        
                        import re
                        cleaned_year_str = re.sub(r"[^0-9]", "", western_year_str)
                        if cleaned_year_str:
                            edu_data_copy["graduation_year"] = int(round(float(cleaned_year_str)))
                        else: # If stripping results in empty, set to None or original? For now, None.
                            edu_data_copy["graduation_year"] = None 
                    except (ValueError, TypeError):
                        edu_data_copy["graduation_year"] = None # If any conversion error, set to None
                coerced_data[key] = _blank_to_none(edu_data_copy, field_info)

            elif key == "contact_info" and isinstance(current_value, dict) and "phone" in current_value:
                contact_data_copy = current_value.copy()
                phone_val = contact_data_copy.get("phone")
                if isinstance(phone_val, list):
                    if phone_val:
                        contact_data_copy["phone"] = str(phone_val[0])
                    else:
                        contact_data_copy["phone"] = None
                coerced_data[key] = _blank_to_none(contact_data_copy, field_info)

            else: # For all other fields not specifically handled
                coerced_data[key] = _blank_to_none(current_value, field_info)
        else:
            # Handle fields from LLM not in the model schema (e.g. log, ignore, or error)
            # For now, we'll ignore them to be robust to extra fields from LLM.
            pass 
    return coerced_data


async def analyse_chat_dynamically(
    chat_df: pd.DataFrame,
    config: Dict[str, Any],
    DynamicModel: Type[BaseModel]
) -> BaseModel:
    """Processes a single chat DataFrame according to the provided dynamic model and config."""
    
    corpus = "\n".join(
        chat_df.loc[chat_df["speaker"] == "participant", "message"].tolist()
    )
    # Truncate corpus if too long
    if len(corpus) > MAX_CORPUS_CHARS:
        corpus = corpus[-MAX_CORPUS_CHARS:]

    # Generate the schema example string from the dynamic model
    schema_example_str = generate_schema_example(DynamicModel)

    # Get the prompt template from the config
    prompt_template = config["prompt_template"]

    # Format the prompt
    # Ensure all required placeholders in the template are available
    prompt_format_args = {
        "chat_id": int(chat_df.iloc[0]["chat_id"]),
        "user_email": chat_df.iloc[0]["user_email"],
        "corpus": corpus,
        "_SCHEMA_EXAMPLE": schema_example_str,
    }
    # Add any other placeholders defined in the schema to prompt_format_args if they exist in chat_df.iloc[0]
    # This makes it flexible if prompts want to use e.g. assistant_id if it's in the schema & data
    for key in DynamicModel.model_fields.keys():
        if key not in prompt_format_args and key in chat_df.iloc[0].index:
            prompt_format_args[key] = chat_df.iloc[0][key]
    
    final_prompt = prompt_template.format(**prompt_format_args)
    
    # Call LLM
    raw_response_json_str = call_llm(final_prompt, str) # Expect raw JSON string

    # Coerce and validate
    coerced_data = _coerce_llm_output(raw_response_json_str, DynamicModel)

    # Validate with the dynamic model
    # Pydantic will raise a ValidationError if the coerced_data doesn't match the DynamicModel fields/types
    try:
        final_data_for_model = coerced_data.copy()
        if "chat_id" not in final_data_for_model and "chat_id" in chat_df.iloc[0].index:
             final_data_for_model["chat_id"] = int(chat_df.iloc[0]["chat_id"])
        
        # Fallback for user_email if not provided by LLM but present in CSV
        if "user_email" not in final_data_for_model or final_data_for_model.get("user_email") is None:
            if "user_email" in chat_df.iloc[0].index and pd.notna(chat_df.iloc[0]["user_email"]):
                final_data_for_model["user_email"] = chat_df.iloc[0]["user_email"]
            else:
                # If still None and it's a required field in the model, provide a placeholder
                if "user_email" in DynamicModel.model_fields and not DynamicModel.model_fields["user_email"].is_required() is False: # Check if it's required
                     if final_data_for_model.get("user_email") is None: # If truly None after all attempts
                        final_data_for_model["user_email"] = "unknown@example.com" # Placeholder

        # Ensure 'extracted_at' is always set to a valid datetime if the field exists in the model.
        # This overrides any null from LLM or if it's missing.
        if 'extracted_at' in DynamicModel.model_fields:
            from datetime import datetime
            final_data_for_model['extracted_at'] = datetime.utcnow().isoformat()

        instance = DynamicModel.model_validate(final_data_for_model)
    except Exception as e: # Catch Pydantic validation errors or others
        # Log error, potentially save problematic response for debugging
        print(f"Error validating LLM output for chat_id {prompt_format_args.get('chat_id')}: {e}")
        print(f"Raw LLM response: {raw_response_json_str}")
        print(f"Coerced data: {coerced_data}")
        # Depending on desired behavior, either raise e, or return a partially filled/default model
        # For now, let's try to create a model with what we have, or an empty one if critical fields missing
        try:
            # Attempt to create a model with as much valid data as possible, ignoring extra fields
            # This is a simplistic fallback.
            valid_data_for_fallback = {k: v for k, v in final_data_for_model.items() if k in DynamicModel.model_fields}
            if "chat_id" not in valid_data_for_fallback:
                 valid_data_for_fallback["chat_id"] = int(chat_df.iloc[0]["chat_id"])
            
            # Fallback for user_email in fallback model creation
            if "user_email" not in valid_data_for_fallback or valid_data_for_fallback.get("user_email") is None:
                if "user_email" in chat_df.iloc[0].index and pd.notna(chat_df.iloc[0]["user_email"]):
                    valid_data_for_fallback["user_email"] = chat_df.iloc[0]["user_email"]
                else:
                    if "user_email" in DynamicModel.model_fields and not DynamicModel.model_fields["user_email"].is_required() is False:
                        if valid_data_for_fallback.get("user_email") is None:
                            valid_data_for_fallback["user_email"] = "unknown@example.com" # Placeholder
            
            # Ensure 'extracted_at' is also set in the fallback if the field exists.
            if 'extracted_at' in DynamicModel.model_fields:
                from datetime import datetime
                valid_data_for_fallback['extracted_at'] = datetime.utcnow().isoformat()

            instance = DynamicModel.model_validate(valid_data_for_fallback)
        except Exception as fallback_e:
            print(f"Fallback model creation failed for chat_id {prompt_format_args.get('chat_id')}: {fallback_e}")
            # Create a minimal instance if all else fails, to prevent crashing the whole batch
            # Requires chat_id and user_email to be in the DynamicModel schema for this to work.
            # This part needs to be robust: ensure critical identifying fields are present.
            minimal_data = {
                "chat_id": int(chat_df.iloc[0]["chat_id"]),
                "user_email": chat_df.iloc[0]["user_email"],
            }
            # Fallback for user_email in minimal_data
            if minimal_data.get("user_email") is None:
                 if "user_email" in DynamicModel.model_fields and not DynamicModel.model_fields["user_email"].is_required() is False:
                    minimal_data["user_email"] = "unknown@example.com"
                 elif "user_email" in DynamicModel.model_fields and DynamicModel.model_fields["user_email"].is_required() is False: # if optional
                     minimal_data["user_email"] = None
                 else: # if required and somehow not caught above, this will likely still fail if no placeholder provided
                     minimal_data["user_email"] = "unknown@example.com"

            # Ensure 'extracted_at' is also set in the minimal_data if the field exists.
            if 'extracted_at' in DynamicModel.model_fields:
                from datetime import datetime
                minimal_data['extracted_at'] = datetime.utcnow().isoformat()
            
            # Add None for all other fields defined in the model to satisfy Pydantic
            # for fields that are truly optional. 'extracted_at' is now handled.
            for field_name in DynamicModel.model_fields:
                if field_name not in minimal_data: # if not chat_id, user_email, or extracted_at (if present)
                    # This assumes other fields are Optional in their schema definition if they can be None.
                    # If a field is required and not 'extracted_at', this minimal_data might still fail.
                    # However, 'extracted_at' was the problematic one.
                    minimal_data[field_name] = None
            instance = DynamicModel.model_validate(minimal_data)
            
    return instance 