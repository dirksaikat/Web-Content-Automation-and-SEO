from sqlalchemy import delete
from sqlmodel import select

from .models import OtpVerification
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import CreateOtpSchema
import uuid


class OtpService:

    async def save_generated_otp(self, otp_schema: CreateOtpSchema, session: AsyncSession):
        await session.exec(
            delete(OtpVerification).where(
                OtpVerification.user_uid == otp_schema.user_uid,
                OtpVerification.purpose == otp_schema.purpose
            )
        )

        await session.commit()

        otp_schema_dict = otp_schema.model_dump()
        otp_verification = OtpVerification(
            **otp_schema_dict
        )
        session.add(otp_verification)
        await session.commit()
        return otp_verification

    async def get_otp_by_user_and_purpose(
            self,
            user_uid: uuid.UUID,
            purpose: str, session: AsyncSession) -> OtpVerification | None:

        statement = (select(OtpVerification).where(
            OtpVerification.user_uid == user_uid,
            OtpVerification.purpose == purpose)
        )
        result = await session.exec(statement=statement)
        otp_entry = result.first()
        return otp_entry

    async def delete_otp(self, user_uid: uuid.UUID, purpose: str, session: AsyncSession):
        pass