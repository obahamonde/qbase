from fastapi import APIRouter, FastAPI

from .qconst import SUMMARY
from .qdoc import app as documents_app
from .qtools import app as tools_app
from .qvector import app as vector_app

api = FastAPI(
    title="QuipuBase",
    description="AI-Driven, Schema-Flexible Document Store",
    summary=SUMMARY,
    version="0.0.1:alpha",
)


def create_app(routers: list[APIRouter] = [documents_app, vector_app, tools_app]):
    """
    Create and configure the QuipuBase API.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    for router in routers:
        api.include_router(router, prefix="/api")

    @api.get("/api/health   ")
    def _():
        return {"code": 200, "message": "QuipuBase is running!"}

    return api
