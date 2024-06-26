from typing import Any

class Quipu:
    def __init__(self, db_path: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    @classmethod
    def count(cls) -> int: ...
    @classmethod
    def get_doc(cls, key: str) -> dict[str, Any] | None: ...
    def put_doc(self, key: str, value: dict[str, Any]) -> None: ...
    @classmethod
    def delete_doc(cls, key: str) -> None: ...
    @classmethod
    def scan_docs(
        cls, limit: int, offset: int, keys_only: bool = False
    ) -> tuple[str, dict[str, Any]]: ...
    @classmethod
    def find_docs(
        cls, limit: int, offset: int, kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]: ...
    def merge_doc(self, key: str, value: dict[str, Any]) -> None: ...
