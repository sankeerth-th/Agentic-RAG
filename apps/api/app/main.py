import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response
from rag_contracts.common import Contract, ErrorResponse

from app.core.config import Settings
from app.core.errors import error_response, register_error_handlers
from app.core.logging import configure_logging
from app.core.openapi import build_openapi
from app.core.services import Services, get_services

logger = logging.getLogger("rag.api")


class HealthResponse(Contract):
    status: Literal["ok"] = "ok"


class ReadyResponse(Contract):
    status: Literal["ready", "unavailable"]
    dependencies: dict[str, Literal["ok", "unavailable"]]


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        application.state.services = Services(settings or Settings())
        try:
            yield
        finally:
            application.state.services.close()

    application = FastAPI(
        title="Agentic RAG Lab",
        version="0.1.0",
        lifespan=lifespan,
        responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    register_error_handlers(application)

    @application.middleware("http")
    async def log_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.request_id = str(uuid4())
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            response = error_response(request, 500, "internal_error", "An internal error occurred")
        response.headers["x-request-id"] = request.state.request_id
        logger.info(
            "http_request",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return response

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @application.get(
        "/ready", response_model=ReadyResponse, responses={503: {"model": ReadyResponse}}
    )
    def ready(
        response: Response, services: Annotated[Services, Depends(get_services)]
    ) -> ReadyResponse:
        checks = services.readiness()
        available = all(checks.values())
        response.status_code = 200 if available else 503
        return ReadyResponse(
            status="ready" if available else "unavailable",
            dependencies={key: "ok" if ok else "unavailable" for key, ok in checks.items()},
        )

    application.openapi = lambda: build_openapi(application)  # type: ignore[method-assign]
    return application


app = create_app()
