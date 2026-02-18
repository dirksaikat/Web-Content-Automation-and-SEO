from sqlalchemy import delete
from sqlmodel import select

from .models import OtpVerification
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import CreateOtpSchema


class OtpService:

    async def save_generated_otp(self, otp_schema: CreateOtpSchema, db: AsyncSession):
        await db.exec(
            delete(OtpVerification).where(
                OtpVerification.user_id == otp_schema.user_id,
                OtpVerification.purpose == otp_schema.purpose
            )
        )
        await db.flush()
        otp_schema_dict = otp_schema.model_dump()
        otp_verification = OtpVerification(
            **otp_schema_dict
        )
        db.add(otp_verification)
        await db.flush()
        return otp_verification

    async def get_otp_by_email_and_purpose(
            self,
            email: str,
            code: str,
            purpose: str, db: AsyncSession) -> OtpVerification | None:
        statement = (select(OtpVerification).where(
            OtpVerification.email == email,
            OtpVerification.token_digest == code,
            OtpVerification.purpose == purpose)
        )
        result = await db.exec(statement=statement)
        otp_entry = result.first()
        return otp_entry

    async def delete_otp(self, email: str, code: str, purpose: str, db: AsyncSession) -> bool:
        await db.exec(
            delete(OtpVerification).where(
                OtpVerification.email == email,
                OtpVerification.purpose == purpose,
                OtpVerification.token_digest == code
            )
        )
        await db.flush()
        return True
