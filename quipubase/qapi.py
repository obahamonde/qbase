from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query, status

from .qschemas import Action, TypeDef, create_model_from_json_schema
from .qvector import app as vector_app


def create_app() -> FastAPI:
    app = FastAPI(
        title="QuipuBase: The AI-Driven, Schema-Flexible Document Store",
        description="QuipuBase is a state-of-the-art document store engineered for performance and flexibility. It is built on a foundation of `json_schema`, a widely recognized standard that allows for highly customizable data structuring. QuipuBase excels in resource constraint environments demanding low latency and high-throughput data management.",
        summary="`json_schema` is a well recognized standard for defining flexible API schemas, QuipuBase leverages this standard  to provide an intuitive an very flexible API where you can tailor the shape of your data according to your needs with access to a rich set of features such as Retrieval Augmented Generation and Function Calling enabling seamless integrations and agent based workflows.",
        version="0.0.1:early-access",
    )

    @app.get("/api/health   ")
    def _():
        return dict(code=200, message="Healthy")

    @app.post("/api/qcollections/{namespace}")
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
        klass = create_model_from_json_schema(definition.definition)
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
        elif action == "getDoc":
            if key is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Key must be provided for action `getDoc`",
                )
            return klass.get_doc(key=key)
        elif action == "deleteDoc":
            if key is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Key must be provided for action `deleteDoc`",
                )
            return klass.delete_doc(key=key)
        elif action == "scanDocs":
            return klass.scan_docs(limit=limit or 1000, offset=offset or 0)
        elif action == "countDocs":
            return klass.count()
        elif action == "existsDoc":
            if key is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Key must be provided for action `existsDoc`",
                )
            return klass.exists(key=key)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action `{action}`",
            )

    app.include_router(vector_app, tags=["vectors"])
    return app
