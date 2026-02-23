from typing import Any, Callable
from fastapi.requests import Request
from fastapi.responses import JSONResponse

def create_exception_handler(status_code: int, initial_detail: Any) -> (
        Callable)[[Request, Exception], JSONResponse]:
    async def exception_handler(request: Request, ex: Exception):
        return JSONResponse(
            content=initial_detail,
            status_code=status_code
        )

    return exception_handler
