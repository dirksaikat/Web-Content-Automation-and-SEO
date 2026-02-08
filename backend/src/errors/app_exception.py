from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any


@dataclass(frozen=True, slots=True)
class ErrorDef:
    code: str
    status: int
    message: str
    internal_message: str | None = None  # logs only


class AppException(Exception):

    def __init__(
            self,
            error: ErrorDef,
            *,
            message: str | None = None,
            internal_message: str | None = None,
            details: dict[str, Any] | None = None,
    ):
        self.code = error.code
        self.status_code = error.status
        self.message = message or error.message
        self.internal_message = internal_message or error.internal_message
        self.details = details
        self.timestamp = datetime.now(UTC).isoformat()

        # Exception message should NEVER leak internals
        super().__init__(self.message)

    def to_dict(self, request_id: str | None = None) -> dict[str, Any]:
        error_dict: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "timestamp": self.timestamp,
        }
        if self.details:
            error_dict["details"] = self.details
        if request_id:
            error_dict["request_id"] = request_id
        return {"error": error_dict}

    def __repr__(self) -> str:
        return f"AppException(code={self.code}, message={self.message!r})"
