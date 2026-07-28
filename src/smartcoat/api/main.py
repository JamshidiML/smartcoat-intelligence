from __future__ import annotations

from collections.abc import Awaitable, Callable
from threading import Lock
from typing import Any

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import Response

from smartcoat.api.knowledge_v2_errors import install_knowledge_v2_error_handling
from smartcoat.api.routes import decisions, events, health, knowledge
from smartcoat.core.config import get_settings

_v2_router_lock = Lock()


def _include_knowledge_v2_router(application: FastAPI) -> None:
    if getattr(application.state, "knowledge_v2_router_loaded", False):
        return
    with _v2_router_lock:
        if getattr(application.state, "knowledge_v2_router_loaded", False):
            return
        from smartcoat.api.routes import knowledge_v2

        application.include_router(knowledge_v2.router)
        application.state.knowledge_v2_router_loaded = True
        application.openapi_schema = None


class SmartCoatAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:
        if self.openapi_schema is None:
            _include_knowledge_v2_router(self)
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                description=self.description,
                routes=self.routes,
            )
        return self.openapi_schema


def create_app() -> FastAPI:
    settings = get_settings()
    application = SmartCoatAPI(
        title=settings.app_name,
        version="0.1.0",
        description="SmartCoat Knowledge Capture MVP API",
    )
    install_knowledge_v2_error_handling(application)
    application.include_router(health.router)
    application.include_router(knowledge.router)
    application.include_router(decisions.router)
    application.include_router(events.router)

    @application.middleware("http")
    async def load_v2_router_for_v2_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path.startswith("/api/v2/knowledge"):
            _include_knowledge_v2_router(application)
        return await call_next(request)

    return application


app = create_app()
