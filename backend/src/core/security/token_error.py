from src.core.exceptions.app_exception import AppException
from src.core.exceptions.app_exception import ErrorDef
from fastapi import status


AUTH_TOKEN_EXPIRED = ErrorDef(
    code="AUTH_TOKEN_EXPIRED",
    status=status.HTTP_401_UNAUTHORIZED,
    message="Token has expired",
)

AUTH_TOKEN_INVALID = ErrorDef(
    code="AUTH_TOKEN_INVALID",
    status=status.HTTP_401_UNAUTHORIZED,
    message="Token is invalid.",
)


class TokenError:

    @staticmethod
    def token_expired() -> AppException:
        return AppException(AUTH_TOKEN_EXPIRED)

    @staticmethod
    def token_invalid(message: str = None) -> AppException:
        return AppException(AUTH_TOKEN_INVALID, message=message)
