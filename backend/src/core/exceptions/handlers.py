from fastapi import FastAPI, Request, status
from src.core.exceptions.app_exception import AppException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from redis.exceptions import RedisError
from .db_error import DatabaseError
from .cache_error import CacheError, InternalError


def _status_to_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_FAILED",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


def _build_error_response(
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict | None = None,
    fields: dict | None = None,
) -> dict:
    from datetime import UTC, datetime

    error_dict: dict = {
        "code": code,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    if request_id:
        error_dict["request_id"] = request_id

    if details:
        error_dict["details"] = details

    if fields:
        error_dict["fields"] = fields

    return {"error": error_dict}


def _get_request_id(request: Request) -> str | None:
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    return request.headers.get("X-Request-Id")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = _get_request_id(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(request_id=request_id),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:

    request_id = _get_request_id(request)

    code = _status_to_code(exc.status_code)

    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", exc.detail.get("error", str(exc.detail)))
        details = {k: v for k, v in exc.detail.items() if k not in ("message", "error")}
    else:
        message = str(exc.detail) if exc.detail else "An error occurred"
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_response(
            code=code,
            message=message,
            request_id=request_id,
            details=details if details else None,
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:

    request_id = _get_request_id(request)

    fields: dict[str, list[str]] = {}
    for error in exc.errors():
        loc = error.get("loc", [])
        if len(loc) > 1:
            field = ".".join(str(loc_part) for loc_part in loc[1:])  # Skip "body" prefix
        elif loc:
            field = str(loc[0])
        else:
            field = "unknown"

        message = error.get("msg", "Invalid value")

        if field not in fields:
            fields[field] = []
        fields[field].append(message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_build_error_response(
            code="VALIDATION_FAILED",
            message="Validation failed",
            request_id=request_id,
            fields=fields,
        ),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:

    request_id = _get_request_id(request)

    if isinstance(exc, IntegrityError):
        error = DatabaseError.integrity_error()
    elif isinstance(exc, OperationalError):
        error = DatabaseError.connection_failed()
    else:
        error = DatabaseError.query_failed()

    return JSONResponse(
        status_code=error.status_code,
        content=error.to_dict(request_id=request_id),
    )


async def redis_exception_handler(request: Request, exc: RedisError) -> JSONResponse:

    request_id = _get_request_id(request)

    error = CacheError.connection_failed()
    return JSONResponse(
        status_code=error.status_code,
        content=error.to_dict(request_id=request_id),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    request_id = _get_request_id(request)

    error = InternalError.ERROR

    return JSONResponse(
        status_code=error.status_code,
        content=error.to_dict(request_id=request_id),
    )


def register_exception_handlers(app: FastAPI) -> None:

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    #app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(RedisError, redis_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)