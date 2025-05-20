"""Dynamically create Pydantic models from configuration."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Type, Union, ForwardRef

import yaml
from pydantic import BaseModel, EmailStr, Field, create_model, BeforeValidator
from typing_extensions import Annotated # For Pydantic V2 Annotated types
from pydantic.fields import FieldInfo

from etl.models import Likert # Assuming Likert is still relevant

def parse_arabic_likert_string(value: Any) -> Any:
    if isinstance(value, float):
        num = round(value)
        return max(1, min(5, num)) # Clamp to 1-5 range
    if isinstance(value, str):
        import re
        match = re.search(r"\d+", value)
        if match:
            try:
                num = int(match.group(0))
                return max(1, min(5, num)) # Clamp to 1-5 range
            except ValueError:
                # If conversion to int fails, return original to let standard validation fail
                return value 
    return value

# Type mapping from YAML string to Python/Pydantic types
# Needs to handle Optional via "type | None" string parsing
# and nested models via recursion or ForwardRef
TYPE_MAP: Dict[str, Type[Any] | object] = {
    "int": int,
    "str": str,
    "bool": bool,
    "float": float,
    "datetime": datetime,
    "EmailStr": EmailStr,
    "Likert": Annotated[Likert, BeforeValidator(parse_arabic_likert_string)],
    # Add other custom types if needed
}

def _parse_type_string(type_str: str, model_name_prefix: str = "") -> Any:
    """Parses a type string (e.g., "str | None", "List[int]") into a Python type or Pydantic FieldInfo."""
    type_str = type_str.strip()
    is_optional = "| None" in type_str
    if is_optional:
        type_str = type_str.replace("| None", "").strip()

    if type_str in TYPE_MAP:
        actual_type = TYPE_MAP[type_str]
    else:
        # Fallback for unrecognised simple types or potentially complex ones not yet handled
        # This might need improvement for more complex scenarios like List[CustomType]
        try:
            actual_type = eval(type_str, {}, {**TYPE_MAP, **globals(), "Optional": Optional, "Union": Union})
        except NameError:
            # If a type is not found, it might be a forward reference to a nested model
            # that will be created later. This is common in Pydantic for circular dependencies
            # or when defining models out of order.
            actual_type = ForwardRef(f"{model_name_prefix}{type_str}")
        except Exception as e:
            raise ValueError(f"Unsupported or malformed type string: {type_str}. Error: {e}")

    if is_optional:
        return Optional[actual_type]
    return actual_type

def create_dynamic_model(model_name: str, schema_config: Dict[str, Any]) -> Type[BaseModel]:
    """Creates a Pydantic model dynamically from a schema configuration.

    Args:
        model_name: The name for the new Pydantic model.
        schema_config: A dictionary where keys are field names and values are either
                       type strings (e.g., "str | None") or nested schema dicts.

    Returns:
        A dynamically created Pydantic BaseModel class.
    """
    fields: Dict[str, Any] = {}
    nested_models: Dict[str, Type[BaseModel]] = {}

    # First pass: create ForwardRefs for all potential nested models
    for field_name, type_info in schema_config.items():
        if isinstance(type_info, dict):
            # It's a nested model. We'll define it later, but declare a ForwardRef for now.
            # The actual nested model name will be prefixed to avoid naming collisions.
            nested_model_name = f"{model_name}_{field_name.capitalize()}"
            # The type in the parent model will be this ForwardRef.
            # fields[field_name] = (ForwardRef(f"'{nested_model_name}'"), FieldInfo(default=None) if "None" in str(type_info) else ...)
            # This part is tricky with dynamic optionality for nested models.
            # For simplicity, let's assume nested models can be optional if any of their fields can be.
            # A more robust way would be to have an explicit "optional: true" in the YAML for nested structures.

    # Second pass: define fields and create actual nested models
    for field_name, type_info in schema_config.items():
        if isinstance(type_info, dict):
            # It's a nested model
            nested_model_name = f"{model_name}_{field_name.capitalize()}"
            nested_model_class = create_dynamic_model(nested_model_name, type_info)
            nested_models[nested_model_name] = nested_model_class
            # Determine if the nested model itself should be optional.
            # Heuristic: if all fields in the nested model are optional, or if it's an empty dict,
            # consider making the field for the nested model optional in the parent.
            # This logic can be refined based on how optionality of nested structures is defined in YAML.
            is_nested_optional = all("| None" in str(v) for v in type_info.values()) if type_info else True
            if is_nested_optional:
                 fields[field_name] = (Optional[nested_model_class], Field(default_factory=lambda: None))
            else:
                 fields[field_name] = (nested_model_class, Field(default_factory=dict)) # Or require it if not optional

        elif isinstance(type_info, str):
            # It's a simple type string
            parsed_type = _parse_type_string(type_info, model_name_prefix=f"{model_name}_")
            if isinstance(parsed_type, ForwardRef) or (hasattr(parsed_type, "__origin__") and parsed_type.__origin__ is Union and any(isinstance(arg, ForwardRef) for arg in parsed_type.__args__)):
                # Handle Optional[ForwardRef(...)] or simple ForwardRef(...)
                default_value = Field(default=None)
            elif "| None" in type_info or type_info.endswith("?") : # Check for optional flag
                default_value = Field(default=None)
            else:
                default_value = Field(...)
            fields[field_name] = (parsed_type, default_value)
        else:
            raise ValueError(f"Invalid schema config for field '{field_name}'. Expected type string or dict.")

    # Create the main model
    DynamicModel = create_model(model_name, **fields) # type: ignore

    # Update forward refs for any nested models within this scope
    # Pydantic V2 typically handles ForwardRef resolution more automatically.
    # The nested_models created should be resolvable if they are in scope.
    DynamicModel.model_rebuild(force=True)

    # For nested models, ensure their ForwardRefs are also resolved.
    # They are already created and should be part of the module's globals directly or indirectly.
    for _nested_name, nested_model_cls in nested_models.items():
        nested_model_cls.model_rebuild(force=True)

    return DynamicModel

def load_config_and_create_model(config_path: str) -> Type[BaseModel]:
    """Loads YAML config and creates a dynamic Pydantic model."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    model_name = config.get("model_name", "DynamicSurveyModel")
    schema_config = config.get("schema", {})
    if not schema_config:
        raise ValueError("Schema configuration is missing or empty in the YAML file.")

    return create_dynamic_model(model_name, schema_config)

def generate_schema_example(model: Type[BaseModel]) -> str:
    """Generates a JSON string representation of the model schema for use in prompts."""
    import json
    # Simplified schema for prompt, focusing on field names and types
    # Pydantic's model_json_schema() is comprehensive but can be verbose for a prompt.
    # This creates a simpler { "field": "type" } representation.
    
    schema_dict = {}
    for field_name, field_info in model.model_fields.items():
        type_repr = str(field_info.annotation)
        # Clean up type representation for readability in prompt
        type_repr = type_repr.replace('typing.Optional[', 'Optional[')
        type_repr = type_repr.replace('pydantic.types.', '') # Clean up pydantic type paths
        type_repr = type_repr.replace("<class '", "").replace("'>", "") # Clean class tags
        if type_repr.startswith("etl.models."):
            type_repr = type_repr.split('.')[-1] # e.g. etl.models.Likert -> Likert

        schema_dict[field_name] = type_repr
        
    return json.dumps(schema_dict, indent=2) 