from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, ClassVar, List, Literal, Optional, TypeVar
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field
from typing_extensions import ParamSpec, Self, TypedDict

from .quipubase import Quipu  # pylint: disable=E0611
from .qutils import handle

A = TypeVar("A")
P = ParamSpec("P")


class _Base(BaseModel):
    def __str__(self) -> str:
        return self.model_dump_json()

    def __repr__(self) -> str:
        return self.model_dump_json()


class Status(_Base):
    code: int
    message: str
    key: Optional[str] = Field(default=None)


class Property(TypedDict):
    type: str
    description: Optional[str]
    default: Optional[Any]
    enum: Optional[List[str]]
    items: Optional[Property]
    properties: Optional[Property]
    required: Optional[List[str]]
    additionalProperties: Optional[bool]


class Function(TypedDict):
    name: str
    type: Literal["function"]
    description: str
    arguments: Property
    required: Optional[List[str]]


T = TypeVar("T", bound="QDocument")


class QDocument(_Base):
    _db_instances: ClassVar[dict[str, Quipu]] = {}
    key: str = Field(default_factory=lambda: str(uuid4()))

    @classmethod
    def __init_subclass__(cls, **kwargs: Any):
        os.makedirs("db", exist_ok=True)
        os.makedirs(f"db/{cls.__name__}", exist_ok=True)
        super().__init_subclass__(**kwargs)

        if cls.__name__ not in cls._db_instances:
            cls._db_instances[cls.__name__] = Quipu(f"db/{cls.__name__}")
        cls._db = cls._db_instances[cls.__name__]

    @handle
    def put_doc(self) -> Status:
        if self._db.exists(key=self.key):
            self._db.merge_doc(self.key, self.model_dump())
        self._db.put_doc(self.key, self.model_dump())
        return Status(code=201, message="Document created", key=self.key)

    @classmethod
    @handle
    def get_doc(cls, *, key: str) -> Optional[Self]:
        data = cls._db.get_doc(key=key)
        if data:
            return cls(**data)
        return None

    @handle
    def merge_doc(self) -> Status:
        self._db.merge_doc(key=self.key, value=self.model_dump())
        return Status(code=200, message="Document updated", key=self.key)

    @classmethod
    @handle
    def delete_doc(cls, *, key: str) -> Status:
        cls._db.delete_doc(key=key)
        return Status(code=204, message="Document deleted", key=key)

    @classmethod
    @handle
    def scan_docs(cls, *, limit: int = 1000, offset: int = 0) -> List[Self]:
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.scan_docs(limit, offset)
        ]

    @classmethod
    @handle
    def find_docs(cls, limit: int = 1000, offset: int = 0, **kwargs: Any) -> List[Self]:
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.find_docs(limit, offset, kwargs)
        ]

    @classmethod
    @handle
    def count(cls) -> int:
        return cls._db.count()

    @classmethod
    @handle
    def exists(cls, *, key: str) -> bool:
        return cls._db.exists(key=key)


class Tool(_Base, ABC):
    @classmethod
    def definition(cls):
        return Function(
            name=cls.__name__,
            type="function",
            description=cls.__doc__ or "[No description provided]",
            arguments=cls.model_json_schema().get("properties", {}),
            required=list(cls.model_json_schema().get("required", [])),
        )

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        pass


class Embedding(QDocument, ABC):
    @abstractmethod
    async def embed(self, *, content: str) -> NDArray[Any]:
        pass

    @abstractmethod
    async def query(
        self,
        *,
        value: NDArray[np.float32],
    ) -> list[Any]:
        pass

    @abstractmethod
    async def upsert(self, *, content: str | list[str]) -> None:
        pass
