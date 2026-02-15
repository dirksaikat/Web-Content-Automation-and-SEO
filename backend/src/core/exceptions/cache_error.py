from src.core.exceptions.app_exception import AppException
from src.core.exceptions.app_exception import ErrorDef
from fastapi import status

CACHE_CONNECTION_FAILED = ErrorDef(
    code="CACHE_CONNECTION_FAILED",
    status=status.HTTP_503_SERVICE_UNAVAILABLE,
    message="Cache connection failed",
)


class CacheError:
    @staticmethod
    def connection_failed() -> AppException:
        return AppException(CACHE_CONNECTION_FAILED)


INTERNAL_ERROR = ErrorDef(
    code="INTERNAL_ERROR",
    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    message="An unexpected error occurred",
)


class InternalError:
    @staticmethod
    def internal_error() -> AppException:
        return AppException(INTERNAL_ERROR)




