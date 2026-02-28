from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.main import get_session
from src.features.otp.request_schemas import (
    VerifyAccountRequestSchema,
    ResendAccountVerificationOptRequestSchema
)
from src.features.otp.response_schemas import (
    EmailVerificationResponseSchema,
    ResendOTPResponse
)
from src.features.auth.user_repository import UserRepository
from src.features.otp.otp_repository import OtpRepository
from src.features.otp.repositories_di import get_otp_repository
from src.features.otp.otp_utils import create_otp_schema
from src.features.otp.otp_utils import verify_code_matches
from src.util.email_util import validate_email
from src.features.auth.auth_error import AuthError
from src.features.otp.otp_utils import hash_otp
from src.infra.rate_limiter import get_rate_limiter, RateLimiter
from src.features.auth.repositories_di import get_user_repository
from src.core.utils.constants import OTP_PURPOSE_ACCOUNT_VERIFICATION
from datetime import datetime, UTC
from src.core.utils.constants import OTP_EXPIRY_IN_MINUTES
from src.mail.mail import send_mail_message
from src.core.utils.constants import (
    RATE_LIMIT_SCOPE_KEY_OTP_ACCOUNT_VERIFICATION,
    RATE_LIMIT_SCOPE_KEY_RESEND_OTP
)

otp_route = APIRouter()


@otp_route.post("/verify-account")
async def verify_account(
        request: Request,
        data: VerifyAccountRequestSchema,
        db: AsyncSession = Depends(get_session),
        user_repository: UserRepository = Depends(get_user_repository),
        otp_repository: OtpRepository = Depends(get_otp_repository),
        rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> EmailVerificationResponseSchema:

    is_rate_limited = await rate_limiter.is_rate_limited(
        scope=RATE_LIMIT_SCOPE_KEY_OTP_ACCOUNT_VERIFICATION, request=request
    )
    if is_rate_limited:
        raise AuthError.rate_limited()

    email = data.email
    email_validation = await validate_email(email)
    if not email_validation["valid"]:
        raise AuthError.invalid_email(errors=email_validation["errors"])

    otp_entry = await otp_repository.get_otp_by_email_and_purpose(
        email=data.email, code=hash_otp(data.otp), purpose=OTP_PURPOSE_ACCOUNT_VERIFICATION, db=db)

    if (
            not otp_entry
            or otp_entry.is_expired()
            or not verify_code_matches(code=data.otp, stored_digest=otp_entry.token_digest)
    ):
        await otp_repository.delete_otp(
            email=data.email, code=data.otp, purpose=OTP_PURPOSE_ACCOUNT_VERIFICATION, db=db
        )
        await db.commit()
        raise AuthError.invalid_otp()

    user = await user_repository.get_user_by_email(email=data.email, db=db)
    if not user:
        raise AuthError.user_not_found()

    await user_repository.update_user(user=user, is_verified=True, db=db)

    await otp_repository.delete_otp(
        email=data.email, code=hash_otp(data.otp), purpose=OTP_PURPOSE_ACCOUNT_VERIFICATION,db=db
    )
    await db.commit()
    return EmailVerificationResponseSchema(
        message="Email verified successfully!",
        email_verified=True
    )


@otp_route.post("/resend-account-verification")
async def resend_account_verification_otp(
    request: Request,
    data: ResendAccountVerificationOptRequestSchema,
    db: AsyncSession = Depends(get_session),
    user_repository: UserRepository = Depends(get_user_repository),
    otp_repository: OtpRepository = Depends(get_otp_repository),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ResendOTPResponse:

    is_rate_limited = await rate_limiter.is_rate_limited(
        scope=RATE_LIMIT_SCOPE_KEY_RESEND_OTP, request=request
    )
    if is_rate_limited:
        raise AuthError.rate_limited()

    email_validation = await validate_email(data.email)
    if not email_validation["valid"]:
        raise AuthError.invalid_email(errors=email_validation["errors"])

    user = await user_repository.get_user_by_email(email=data.email, db=db)
    if not user:
        raise AuthError.user_not_found()

    if user.is_verified:
        return ResendOTPResponse(
            message="This email is already verified. You can log in.",
            active_otp=False,
            expires_in_seconds=0,
        )

    if not user.is_active:
        raise AuthError.account_inactive()

    active_otp = await otp_repository.get_active_otp(
        email=data.email, purpose=OTP_PURPOSE_ACCOUNT_VERIFICATION, db=db
    )

    if active_otp:
        utc_now = datetime.now(UTC)
        if utc_now < active_otp.resend_available_at:
            wait_delta = active_otp.resend_available_at - utc_now
            wait_seconds = int(wait_delta.total_seconds())
            wait_minutes = wait_seconds // 60
            wait_secs = wait_seconds % 60

            return ResendOTPResponse(
                message=f"Please check your email for the verification code. You can request a new code in {wait_minutes}m {wait_secs}s.",
                active_otp=True,
                cooldown_remaining_seconds=wait_seconds,
            )

        await otp_repository.delete_expired_otp(email=data.email, purpose=OTP_PURPOSE_ACCOUNT_VERIFICATION, db=db)

    otp_schema = create_otp_schema(
        email=data.email, user_id=user.id, purpose=OTP_PURPOSE_ACCOUNT_VERIFICATION
    )
    await otp_repository.save_generated_otp(otp_schema=otp_schema, db=db)

    await db.commit()

    html = f"<h1>Your otp is {otp_schema.code} </h1>"

    await send_mail_message(
        recipients=[data.email],
        subject="OTP Verification",
        body=html
    )

    return ResendOTPResponse(
        message="Verification code sent to your email.",
        active_otp=True,
        cooldown_remaining_seconds=OTP_EXPIRY_IN_MINUTES*60,
    )
