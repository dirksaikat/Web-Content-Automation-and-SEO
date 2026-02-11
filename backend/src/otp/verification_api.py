from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from .schemas import AccountVerificationSchema
from src.auth.service import UserService
from .service import OtpService
from src.otp.otp_utils import verify_code_matches
from src.util.email_util import validate_email
from src.errors.auth_error import AuthError
from .otp_utils import hash_otp


otp_route = APIRouter()
user_service = UserService()
otp_service = OtpService()


@otp_route.post("/verify-account")
async def verify_account(data: AccountVerificationSchema, session: AsyncSession = Depends(get_session)):
    email = data.email
    email_validation = await validate_email(email)
    if not email_validation["valid"]:
        raise AuthError.invalid_email(errors=email_validation["errors"])

    normalised_email = email_validation["normalized"]

    otp_entry = await otp_service.get_otp_by_email_and_purpose(
        email=normalised_email, code=hash_otp(data.otp), purpose="account_verification", session=session)

    if (
            not otp_entry
            or otp_entry.is_expired()
            or not verify_code_matches(code=data.otp, stored_digest=otp_entry.token_digest)
    ):
        await otp_service.delete_otp(email=normalised_email, code=data.otp,
                                     purpose="account_verification", session=session)
        raise AuthError.invalid_otp()

    user = await user_service.get_user_by_email(email=normalised_email, session=session)
    if not user:
        raise AuthError.user_not_found()

    # 5. Update user as verified
    await user_service.update_user(user=user, session=session, is_verified=True)

    await otp_service.delete_otp(email=normalised_email, code=hash_otp(data.otp), purpose="account_verification", session=session)

    return {
        "message": "Otp verified"
    }
