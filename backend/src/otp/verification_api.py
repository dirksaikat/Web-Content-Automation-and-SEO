from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from .schemas import AccountVerificationSchema
from src.auth.service import UserService
from .service import OtpService
from src.errors.errors import UserNotFound
from src.otp.otp_utils import verify_code_matches
from src.errors.errors import InvalidOtp


otp_route = APIRouter()
user_service = UserService()
otp_service = OtpService()


@otp_route.post("/verify-account")
async def verify_account(data: AccountVerificationSchema, session: AsyncSession = Depends(get_session)):
    email = data.email
    user = await user_service.get_user_by_email(email=email, session=session)
    if not user:
        raise UserNotFound()

    otp_entry = await otp_service.get_otp_by_user_and_purpose(
        user_uid=user.uid, purpose="account_verification", session=session)

    if (
            not otp_entry
            or otp_entry.is_expired()
            or not verify_code_matches(data.otp, otp_entry.salt, otp_entry.token_digest)
    ):
        await otp_service.delete_otp(user_uid=user.uid, purpose="account_verification", session=session)
        raise InvalidOtp()

    await otp_service.delete_otp(user_uid=user.uid, purpose="account_verification", session=session)

    # 5. Update user as verified
    # await self.user_service.mark_user_as_verified(
    #     user_uid=user_uid,
    #     session=session
    # )

    return {
        "message": "Otp verified"
    }
