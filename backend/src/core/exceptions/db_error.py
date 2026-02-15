from src.core.exceptions.app_exception import AppException
from src.core.exceptions.app_exception import ErrorDef
from fastapi import status


IntegrityError = ErrorDef(
    code="IntegrityError",
    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    message="DB Integrity Error",
)

CONNECTION_FAILED = ErrorDef(
    code="CONNECTION_FAILED",
    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    message="DB Connection Failed",
)

QUERY_FAILED = ErrorDef(
    code="QUERY_FAILED",
    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    message="DB Query Failed",
)

class DatabaseError:
    @staticmethod
    def integrity_error() -> AppException:
        return AppException(IntegrityError)

    @staticmethod
    def connection_failed() -> AppException:
        return AppException(CONNECTION_FAILED)

    @staticmethod
    def query_failed() -> AppException:
        return AppException(QUERY_FAILED)
