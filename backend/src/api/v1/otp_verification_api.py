from fastapi import APIRouter, Depends
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
from src.features.otp.otp_utils import verify_code_matches
from src.util.email_util import validate_email
from src.features.auth.auth_error import AuthError
from src.features.otp.otp_utils import hash_otp
from src.infra.rate_limiter import RateLimitKey, get_rate_limiter
from src.features.auth.repositories_di import get_user_repository
from src.core.utils.constants import OTP_PURPOSE_ACCOUNT_VERIFICATION

otp_route = APIRouter()

register_rate_limiter = get_rate_limiter(
    limit=3,
    window_seconds=60,
    key_type=RateLimitKey.IP,
    block_seconds=3600
)


@otp_route.post("/verify-account")
async def verify_account(
        data: VerifyAccountRequestSchema,
        db: AsyncSession = Depends(get_session),
        user_repository: UserRepository = Depends(get_user_repository),
        otp_repository: OtpRepository = Depends(get_otp_repository),
        _: None = Depends(register_rate_limiter),
) -> EmailVerificationResponseSchema:
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


@otp_route.post("resend-account-verification")
async def resend_account_verification_otp(
    data: ResendAccountVerificationOptRequestSchema,
    db: AsyncSession = Depends(get_session),
    user_repository: UserRepository = Depends(get_user_repository),
    otp_repository: OtpRepository = Depends(get_otp_repository),
) -> ResendOTPResponse:
    #todo check rate limit first

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


    pass