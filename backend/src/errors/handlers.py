from fastapi import FastAPI, Request, status
from .app_exception import AppException
from fastapi.responses import JSONResponse


def _get_request_id(request: Request) -> str | None:
    """Extract request ID from request state or headers."""
    # Try state first (set by RequestIdMiddleware)
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    # Fallback to header
    return request.headers.get("X-Request-Id")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = _get_request_id(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(request_id=request_id),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI app.

    Call this in your create_app() function.
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)