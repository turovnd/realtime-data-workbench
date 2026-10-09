from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from workbench.logic.errors import (
    AuthenticationError,
    ConflictError,
    CursorError,
    CursorExpired,
    RateLimitError,
)
from workbench.settings import Settings


def install_http(app: FastAPI, config: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def guard_mutation(request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST":
            origin = request.headers.get("origin")
            same_origin = str(request.base_url).rstrip("/")
            if (
                origin is not None
                and origin not in config.allowed_origins
                and origin != same_origin
            ):
                return JSONResponse({"detail": "Origin is not allowed"}, status_code=403)
            length = request.headers.get("content-length")
            if length is None or not length.isdigit() or int(length) > 16384:
                return JSONResponse(
                    {"detail": "A request body of at most 16 KiB is required"}, status_code=413
                )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(ConflictError)
    async def conflict(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(RateLimitError)
    async def rate_limit(_request: Request, exc: RateLimitError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=429, headers={"Retry-After": "900"})

    @app.exception_handler(AuthenticationError)
    async def auth_error(_request: Request, _exc: AuthenticationError) -> JSONResponse:
        return JSONResponse({"detail": "Email or password is incorrect"}, status_code=401)

    @app.exception_handler(CursorExpired)
    async def cursor_expired(_request: Request, exc: CursorExpired) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=410)

    @app.exception_handler(CursorError)
    async def cursor_error(_request: Request, exc: CursorError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=400)
