from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.main import get_session
from .schemas import AccountVerificationSchema, EmailVerificationResponseSchema
from src.features.auth.user_repository import UserRepository
from .service import OtpService
from src.otp.otp_utils import verify_code_matches
from src.util.email_util import validate_email
from src.features.auth.auth_error import AuthError
from .otp_utils import hash_otp
from src.infra.rate_limiter import RateLimitKey, get_rate_limiter
from src.features.auth.services_di import get_user_repository

otp_route = APIRouter()
otp_service = OtpService()

register_rate_limiter = get_rate_limiter(
    limit=3,
    window_seconds=60,
    key_type=RateLimitKey.IP,
    block_seconds=3600
)


@otp_route.post("/verify-account")
async def verify_account(data: AccountVerificationSchema,
                         db: AsyncSession = Depends(get_session),
                         user_service: UserRepository = Depends(get_user_repository),
                         _: None = Depends(register_rate_limiter), ) -> EmailVerificationResponseSchema:
    email = data.email
    email_validation = await validate_email(email)
    if not email_validation["valid"]:
        raise AuthError.invalid_email(errors=email_validation["errors"])

    otp_entry = await otp_service.get_otp_by_email_and_purpose(
        email=data.email, code=hash_otp(data.otp), purpose="account_verification", db=db)

    if (
            not otp_entry
            or otp_entry.is_expired()
            or not verify_code_matches(code=data.otp, stored_digest=otp_entry.token_digest)
    ):
        await otp_service.delete_otp(email=data.email, code=data.otp, purpose="account_verification", db=db)
        raise AuthError.invalid_otp()

    user = await user_service.get_user_by_email(email=data.email, db=db)
    if not user:
        raise AuthError.user_not_found()

    await user_service.update_user(user=user, is_verified=True, db=db)

    await otp_service.delete_otp(email=data.email, code=hash_otp(data.otp), purpose="account_verification",db=db)
    await db.commit()
    return EmailVerificationResponseSchema(
        message="Email verified successfully!",
        email_verified=True
    )
