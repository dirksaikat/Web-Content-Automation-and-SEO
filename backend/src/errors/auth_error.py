from .app_exception import AppException
from .app_exception import ErrorDef
from fastapi import status

AUTH_INVALID_CREDENTIALS = ErrorDef(
    code="AUTH_INVALID_CREDENTIALS",
    status=status.HTTP_401_UNAUTHORIZED,
    message="Invalid email or password",
)

AUTH_TOKEN_EXPIRED = ErrorDef(
    code="AUTH_TOKEN_EXPIRED",
    status=status.HTTP_401_UNAUTHORIZED,
    message="Token has expired",
)

AUTH_FORBIDDEN = ErrorDef(
    code="AUTH_FORBIDDEN",
    status=status.HTTP_403_FORBIDDEN,
    message="Access forbidden",
)

AUTH_RATE_LIMITED = ErrorDef(
    code="AUTH_RATE_LIMITED",
    status=status.HTTP_429_TOO_MANY_REQUESTS,
    message="Too many attempts. Please try again later.",
)

USER_EMAIL_INVALID = ErrorDef(
    code="USER_EMAIL_INVALID",
    status=status.HTTP_400_BAD_REQUEST,
    message="Invalid email.",
)

USER_EMAIL_EXISTS = ErrorDef(
    code="USER_EMAIL_EXISTS",
    status=status.HTTP_400_BAD_REQUEST,
    message="This email is already registered.",
)

AUTH_INVALID_PASSWORD = ErrorDef(
    code="AUTH_INVALID_PASSWORD",
    status=status.HTTP_400_BAD_REQUEST,
    message="Password is not valid.",
)

AUTH_USER_NOT_FOUND = ErrorDef(
    code="AUTH_USER_NOT_FOUND",
    status=status.HTTP_400_BAD_REQUEST,
    message="User not found.",
)

AUTH_INVALID_OTP = ErrorDef(
    code="AUTH_INVALID_OTP",
    status=status.HTTP_400_BAD_REQUEST,
    message="Invalid otp.",
)

AUTH_ACCOUNT_LOCKED = ErrorDef(
    code="AUTH_ACCOUNT_LOCKED",
    status=status.HTTP_429_TOO_MANY_REQUESTS,
    message="Account locked due to too many failed attempts.",
)

AUTH_ACCOUNT_INACTIVE = ErrorDef(
    code="AUTH_ACCOUNT_INACTIVE",
    status=status.HTTP_401_UNAUTHORIZED,
    message="Account is inactive",
)

AUTH_EMAIL_NOT_VERIFIED = ErrorDef(
    code="AUTH_EMAIL_NOT_VERIFIED",
    status=status.HTTP_403_FORBIDDEN,
    message="Email is not verified yet.",
)


class AuthError:
    @staticmethod
    def invalid_credentials(**details) -> AppException:
        return AppException(
            AUTH_INVALID_CREDENTIALS,
            details=details or None,
        )

    @staticmethod
    def invalid_email(**details) -> AppException:
        return AppException(
            USER_EMAIL_INVALID,
            details=details or None,
        )

    @staticmethod
    def invalid_password(**details) -> AppException:
        return AppException(
            AUTH_INVALID_PASSWORD,
            details=details or None,
        )

    @staticmethod
    def token_expired() -> AppException:
        return AppException(AUTH_TOKEN_EXPIRED)

    @staticmethod
    def email_already_registered() -> AppException:
        return AppException(USER_EMAIL_EXISTS)

    @staticmethod
    def rate_limited(message: str = None) -> AppException:
        return AppException(error=AUTH_RATE_LIMITED, message=message)

    @staticmethod
    def user_not_found() -> AppException:
        return AppException(error=AUTH_USER_NOT_FOUND)

    @staticmethod
    def invalid_otp() -> AppException:
        return AppException(error=AUTH_INVALID_OTP)

    @staticmethod
    def account_locked(**details) -> AppException:
        return AppException(error=AUTH_ACCOUNT_LOCKED, details=details)

    @staticmethod
    def account_inactive() -> AppException:
        return AppException(error=AUTH_ACCOUNT_INACTIVE)

    @staticmethod
    def account_not_verified() -> AppException:
        return AppException(error=AUTH_EMAIL_NOT_VERIFIED)
