from dataclasses import dataclass
from enum import Enum

from src.core.utils.constants import (
    RATE_LIMIT_SCOPE_KEY_REGISTRATION,
    RATE_LIMIT_SCOPE_KEY_LOGIN,
    RATE_LIMIT_SCOPE_KEY_OTP_ACCOUNT_VERIFICATION,
    RATE_LIMIT_SCOPE_KEY_OTP_FORGOT_PASSWORD,
    RATE_LIMIT_SCOPE_KEY_RESEND_OTP
)


class RateLimitKey(Enum):
    IP = "ip"
    IP_ENDPOINT = "ip_endpoint"
    IP_USERNAME = "ip_username"
    GLOBAL = "global"


@dataclass(frozen=True)
class RateLimitConfig:
    limit: int
    window_seconds: int
    block_seconds: int
    key_type: RateLimitKey


RATE_LIMITS: dict[str, RateLimitConfig] = {
    RATE_LIMIT_SCOPE_KEY_REGISTRATION: RateLimitConfig(
        limit=3,
        window_seconds=60,
        block_seconds=3600,
        key_type=RateLimitKey.IP,
    ),
    RATE_LIMIT_SCOPE_KEY_LOGIN: RateLimitConfig(
        limit=3,
        window_seconds=60,
        block_seconds=3600,
        key_type=RateLimitKey.IP_USERNAME,
    ),
    RATE_LIMIT_SCOPE_KEY_OTP_ACCOUNT_VERIFICATION: RateLimitConfig(
        limit=3,
        window_seconds=60,
        key_type=RateLimitKey.IP,
        block_seconds=3600
    ),
    RATE_LIMIT_SCOPE_KEY_RESEND_OTP: RateLimitConfig(
        limit=3,
        window_seconds=60,
        key_type=RateLimitKey.IP,
        block_seconds=600
    ),

    RATE_LIMIT_SCOPE_KEY_OTP_FORGOT_PASSWORD: RateLimitConfig(
        limit=5,
        window_seconds=3600,
        block_seconds=3600,
        key_type=RateLimitKey.IP_USERNAME,
    ),
}
