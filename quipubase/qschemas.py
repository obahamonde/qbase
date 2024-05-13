from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Type, TypeAlias, Union

from pydantic import BaseModel, Field, create_model  # type: ignore
from typing_extensions import TypedDict

from .qdoc import QDocument

Action: TypeAlias = Literal[
    "putDoc",
    "getDoc",
    "mergeDoc",
    "deleteDoc",
    "findDocs",
    "scanDocs",
    "countDocs",
    "existsDoc",
]

MAPPING = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
    "null": None,
}


def parse_anyof_oneof(schema: Dict[str, Any]) -> Union[Type[QDocument], None]:
    if "anyOf" in schema:
        return Union[
            tuple[type](cast_to_type(sub_schema) for sub_schema in schema["anyOf"])  # type: ignore
        ]
    elif "oneOf" in schema:
        return Union[
            tuple[type](cast_to_type(sub_schema) for sub_schema in schema["oneOf"])  # type: ignore
        ]
    else:
        return None


def create_oneof_validator(fields: List[str]):
    def validate_oneof(cls: Type[QDocument], values: Dict[str, Any]):
        match_count = sum(
            1 for field in fields if field in values and values[field] is not None
        )
        if match_count != 1:
            raise ValueError("Exactly one field must be provided")
        return values

    return validate_oneof


def cast_to_type(schema: Dict[str, Any]) -> Any:
    if "enum" in schema:
        enum_values = tuple(schema["enum"])
        if all(isinstance(value, type(enum_values[0])) for value in enum_values):
            return Literal[enum_values]  # type: ignore
    elif schema.get("type") == "object":
        if schema.get("properties"):
            return create_model_from_json_schema(schema)  # type: ignore
    elif schema.get("type") == "array":
        return List[cast_to_type(schema.get("items", {}))]
    else:
        return MAPPING.get(schema.get("type", "string"), str)
    return Any


def create_model_from_json_schema(
    schema: JsonSchema, partial: bool = False
) -> Type[QDocument]:
    name = schema.get("title", "Model")
    properties = schema.get("properties", {})
    attributes: Dict[str, Any] = {}
    if not partial:
        for key, value in properties.items():
            attributes[key] = (cast_to_type(value), ...)  # type: ignore
    else:
        for key, value in properties.items():
            attributes[key] = (Optional[cast_to_type(value)], None)  # type: ignore
    return create_model(name, __base__=QDocument, **attributes)  # type: ignore


class Property(TypedDict, total=False):
    type: str


class JsonSchema(TypedDict):
    title: str
    type: Literal["object"]
    properties: Dict[str, Property]
    required: List[str]


class TypeDef(BaseModel):
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The data to be stored if the action is `putDoc` or `mergeDoc`",
        examples=[
            {
                "title": "JobPosting",
                "modality": "full-time",
                "location": "Remote",
                "salary": 100000,
                "remote": True,
                "company": {"name": "Acme Inc.", "url": "https://acme.com"},
                "skills": ["python", "fastapi", "aws"],
            }
        ],
    )
    definition: JsonSchema = Field(
        ...,
        description="The `jsonschema` definition of the data, for more information see https://swagger.io/docs/specification/data-models",
        examples=[
            {
                "title": "JobPosting",
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "modality": {
                        "type": "string",
                        "enum": ["full-time", "part-time", "contract"],
                    },
                    "location": {"type": "string"},
                    "salary": {"type": "number"},
                    "remote": {"type": "boolean"},
                    "company": {
                        "type": "object",
                        "title": "Company",
                        "properties": {
                            "name": {"type": "string"},
                            "url": {"type": "string"},
                        },
                    },
                    "skills": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "location", "salary", "company"],
            }
        ],
    )
