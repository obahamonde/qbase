from typing import Optional, Type

from fastapi import APIRouter, Body, FastAPI, HTTPException, Path, Query, status

from .qdoc import QDocument
from .qschemas import Action, TypeDef, create_model_from_json_schema
from .qvector import app as vector_app


def create_class(action: Action, schema: TypeDef) -> Type[QDocument]:
    """
    Create a class from a JSON
    schema definition.

    Args:
        namespace (str): The namespace of the document.
        schema (TypeDef): The JSON schema definition.

    Returns:
        Type[QDocument]: The class created from the schema.
    """
    return create_model_from_json_schema(
        schema.definition, partial=action in ("mergeDoc", "findDocs")
    )


def create_app() -> FastAPI:
    """
    Create and configure the QuipuBase API.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    api = FastAPI(
        title="QuipuBase",
        description="AI-Driven, Schema-Flexible Document Store",
        summary="The `json_schema` standard is well-recognized for defining flexible API schemas, QuipuBase leverages this standard  to provide an intuitive and flexible way to customize the shape of your data, according to your needs with access to a rich set of features such as Retrieval Augmented Generation and Function Calling enabling seamless integrations and agentic workflows on top of essential features such as CRUD operations and search.",
        version="0.0.1:alpha",
    )
    app = APIRouter()

    @app.post("/api/documents/{namespace}")
    def _(
        namespace: str = Path(description="The namespace of the document"),
        action: Action = Query(..., description="The method to be executed"),
        key: Optional[str] = Query(
            None, description="The unique identifier of the document"
        ),
        limit: Optional[int] = Query(
            None, description="The maximum number of documents to return"
        ),
        offset: Optional[int] = Query(
            None, description="The number of documents to skip"
        ),
        definition: TypeDef = Body(...),
    ):

        klass = create_class(action, definition)
        if action in ("putDoc", "mergeDoc", "findDocs"):
            assert (
                definition.data is not None
            ), f"Data must be provided for action `{action}`"
            if action == "putDoc":
                doc = klass(namespace=namespace, **definition.data)  # type: ignore
                return doc.put_doc()
            if action == "mergeDoc":
                doc = klass(namespace=namespace, **definition.data)  # type: ignore
                return doc.merge_doc()
            if action == "findDocs":
                return klass.find_docs(
                    limit=limit or 1000,
                    offset=offset or 0,
                    namespace=namespace,
                    **definition.data,
                )
        if action in ("getDoc", "deleteDoc", "scanDocs", "countDocs", "existsDoc"):
            assert key is not None, f"Key must be provided for action `{action}`"
            if definition.data is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data must not be provided for this action",
                )
            if action == "getDoc":
                return klass.get_doc(key=key)
            if action == "deleteDoc":
                return klass.delete_doc(key=key)
            if action == "scanDocs":
                return klass.scan_docs(limit=limit or 1000, offset=offset or 0)
            if action == "countDocs":
                return klass.count()
            if action == "existsDoc":
                return klass.exists(key=key)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid action `{action}`",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action `{action}`",
            )

    api.include_router(vector_app, tags=["semantic"], prefix="/api")
    api.include_router(app, tags=["document"], prefix="/api")

    @api.get("/api/health   ")
    def _():
        return {"code": 200, "message": "QuipuBase is running!"}

    return api
