from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, create_model  # type: ignore
from typing_extensions import TypedDict, TypeVar

from .qconst import MAPPING, Action

T = TypeVar("T", bound=BaseModel)


class Property(TypedDict):
    type: str
    description: Optional[str]
    default: Optional[Any]
    enum: Optional[List[str]]
    items: Optional[Property]
    properties: Optional[Property]
    required: Optional[List[str]]
    additionalProperties: Optional[bool]


class JsonSchema(TypedDict):
    title: str
    type: Literal["object"]
    properties: Dict[str, Property]
    required: List[str]


def parse_anyof_oneof(schema: Dict[str, Any]) -> Union[Type[BaseModel], None]:
    """
    Parse the 'anyOf' or 'oneOf' schema and return the corresponding Union type.
    """
    if "anyOf" in schema:
        return Union[
            tuple[type](cast_to_type(sub_schema) for sub_schema in schema["anyOf"])  # type: ignore
        ]
    if "oneOf" in schema:
        return Union[
            tuple[type](cast_to_type(sub_schema) for sub_schema in schema["oneOf"])  # type: ignore
        ]
    return None


def cast_to_type(schema: Dict[str, Any]) -> Any:
    """
    Cast the schema to the corresponding Python type.
    """
    if "enum" in schema:
        enum_values = tuple(schema["enum"])
        if all(isinstance(value, type(enum_values[0])) for value in enum_values):
            return Literal[enum_values]  # type: ignore
    elif schema.get("type") == "object":
        if schema.get("properties"):
            return create_class(schema=schema, base=BaseModel, action=None)  # type: ignore
    elif schema.get("type") == "array":
        return List[cast_to_type(schema.get("items", {}))]
    return MAPPING.get(schema.get("type", "string"), str)


def create_class(
    *, schema: JsonSchema, base: Type[T], action: Optional[Action]
) -> Type[T]:
    """
    Create a class based on the schema, base class, and action.
    """
    name = schema.get("title", "Model")
    properties = schema.get("properties", {})
    attributes: Dict[str, Any] = {}
    if action and action in ("putDoc", "mergeDoc", "findDocs") or not action:
        for key, value in properties.items():
            attributes[key] = (cast_to_type(value), ...)  # type: ignore
    elif action and action in (
        "getDoc",
        "deleteDoc",
        "scanDocs",
        "countDocs",
        "existsDoc",
    ):
        for key, value in properties.items():
            attributes[key] = (Optional[cast_to_type(value)], None)  # type: ignore
    elif action:
        raise ValueError(f"Invalid action `{action}`")
    return create_model(name, __base__=base, **attributes)  # type: ignore
