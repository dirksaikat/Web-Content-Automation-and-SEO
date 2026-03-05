from fastapi import APIRouter, Depends, Request
from src.features.auth.request_schema import ForgotPasswordRequest, ResetPasswordRequest
from src.features.auth.response_schema import ResetPasswordResponse
from src.features.otp.response_schemas import (
    OTPResponse
)
from src.features.auth.user_repository import UserRepository
from src.features.otp.otp_repository import OtpRepository
from src.features.otp.repositories_di import get_otp_repository
from src.features.otp.otp_utils import create_otp_schema, hash_otp, verify_code_matches
from src.infra.rate_limiter import get_rate_limiter, RateLimiter
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.main import get_session
from src.features.auth.repositories_di import get_user_repository
from src.core.utils.constants import RATE_LIMIT_SCOPE_KEY_OTP_FORGOT_PASSWORD
from src.features.auth.auth_error import AuthError
from src.util.email_util import validate_email
from src.core.utils.constants import OTP_PURPOSE_FORGOT_PASSWORD, OTP_EXPIRY_IN_MINUTES
from src.mail.mail import send_mail_message
from datetime import datetime, UTC
from src.core.security.password_util import validate_password_strength, hash_password

password_router = APIRouter(prefix="/auth", tags=["Password Management"])


@password_router.post("/forgot-password")
async def forgot_password(
        request_data: ForgotPasswordRequest,
        requests: Request,
        db: AsyncSession = Depends(get_session),
        user_repository: UserRepository = Depends(get_user_repository),
        otp_repository: OtpRepository = Depends(get_otp_repository),
        rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> OTPResponse:

    is_rate_limited = await rate_limiter.is_rate_limited(
        scope=RATE_LIMIT_SCOPE_KEY_OTP_FORGOT_PASSWORD, request=requests
    )
    if is_rate_limited:
        raise AuthError.rate_limited()

    email = request_data.email
    email_validation = await validate_email(email)
    if not email_validation["valid"]:
        raise AuthError.invalid_email(errors=email_validation["errors"])

    user = await user_repository.get_user_by_email(email=str(request_data.email), db=db)

    if not user or not user.is_active or not user.is_verified:
        # Don't reveal that email doesn't exist
        return OTPResponse(message="Password reset code sent.")

    active_otp = await otp_repository.get_active_otp(
        email=request_data.email, purpose=OTP_PURPOSE_FORGOT_PASSWORD, db=db
    )
    if active_otp:
        utc_now = datetime.now(UTC)
        if utc_now < active_otp.resend_available_at:
            wait_delta = active_otp.resend_available_at - utc_now
            wait_seconds = int(wait_delta.total_seconds())
            wait_minutes = wait_seconds // 60
            wait_secs = wait_seconds % 60

            return OTPResponse(
                message=f"Please check your email for the verification code."
                        f" You can request a new code in {wait_minutes}m {wait_secs}s.",
                active_otp=True,
                cooldown_remaining_seconds=wait_seconds,
            )

        await otp_repository.delete_expired_otp(email=request_data.email, purpose=OTP_PURPOSE_FORGOT_PASSWORD, db=db)

    otp_schema = create_otp_schema(
        email=request_data.email, user_id=user.id, purpose=OTP_PURPOSE_FORGOT_PASSWORD
    )
    await otp_repository.save_generated_otp(otp_schema=otp_schema, db=db)
    await db.commit()

    print("xxxxxx")
    print(f"generated otp is {otp_schema.code}")

    html = f"<h1>Your otp is {otp_schema.code} </h1>"
    await send_mail_message(
        recipients=[user.email],
        subject="OTP Verification",
        body=html
    )

    return OTPResponse(
        message="Password reset code sent.",
        active_otp=True,
        expires_in_seconds=OTP_EXPIRY_IN_MINUTES * 60,
    )


@password_router.post("/reset-password")
async def reset_password(
        request_data: ResetPasswordRequest,
        request: Request,
        db: AsyncSession = Depends(get_session),
        user_repository: UserRepository = Depends(get_user_repository),
        otp_repository: OtpRepository = Depends(get_otp_repository),
        rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ResetPasswordResponse:

    email_validation = await validate_email(request_data.email)
    if not email_validation["valid"]:
        raise AuthError.invalid_email(errors=email_validation["errors"])

    pwd_validation = validate_password_strength(request_data.password, request_data.confirm_password)

    if not pwd_validation["valid"]:
        raise AuthError.invalid_password(errors=pwd_validation["errors"])

    otp_entry = await otp_repository.get_otp_by_email_and_purpose(
        email=request_data.email, code=hash_otp(request_data.code), purpose=OTP_PURPOSE_FORGOT_PASSWORD, db=db)

    if not otp_entry or not verify_code_matches(code=request_data.code, stored_digest=otp_entry.token_digest):
        await check_failure_rate_limit(request_data=request_data, request=request, rate_limiter=rate_limiter)
        raise AuthError.invalid_otp()

    if otp_entry.is_expired():
        await check_failure_rate_limit(request_data=request_data, request=request, rate_limiter=rate_limiter)
        await otp_repository.delete_otp(
            email=request_data.email, code=request_data.code, purpose=OTP_PURPOSE_FORGOT_PASSWORD, db=db
        )
        await db.commit()
        raise AuthError.invalid_otp()

    user = await user_repository.get_user_by_email(email=request_data.email, db=db)
    if not user:
        await check_failure_rate_limit(request_data=request_data, request=request, rate_limiter=rate_limiter)
        raise AuthError.user_not_found()

    await user_repository.update_user(user=user, db=db, password_hash=hash_password(request_data.password))

    await otp_repository.delete_otp(
        email=request_data.email, code=request_data.code, purpose=OTP_PURPOSE_FORGOT_PASSWORD, db=db
    )
    await db.commit()

    return ResetPasswordResponse(
        message="Password reset successfully. Please log in with your new password."
    )


async def check_failure_rate_limit(
        request_data: ResetPasswordRequest,
        request: Request,
        rate_limiter: RateLimiter
):
    is_limited = await rate_limiter.is_rate_limited(
        scope=RATE_LIMIT_SCOPE_KEY_OTP_FORGOT_PASSWORD,
        request=request,
        identifier=request_data.email
    )
    if is_limited:
        raise AuthError.rate_limited()
