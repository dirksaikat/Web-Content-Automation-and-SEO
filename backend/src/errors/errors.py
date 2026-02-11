from typing import Any, Callable
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """This is the base class for all exceptions in the project"""
    pass


class InvalidToken(AppException):
    """User ha provided an invalid or expired token"""
    pass


class RevokedToken(AppException):
    """User has provided a token that has been revoked"""
    pass


class AccessTokenRequired(AppException):
    """User has provided a refresh token when an access token is needed"""
    pass


class RefreshTokenRequired(AppException):
    """User has provided an access token when a refresh token is needed"""
    pass

class InvalidCredentials(AppException):
    """Invalid credentials were provided"""
    pass


class InsufficientPermission(AppException):
    """User does not have necessary permissions to that action"""
    pass


class AccountNotVerified(AppException):
    """"""
    pass



def create_exception_handler(status_code: int, initial_detail: Any) -> (
        Callable)[[Request, Exception], JSONResponse]:
    async def exception_handler(request: Request, ex: Exception):
        return JSONResponse(
            content=initial_detail,
            status_code=status_code
        )

    return exception_handler
