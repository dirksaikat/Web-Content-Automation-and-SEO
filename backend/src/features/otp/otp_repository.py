from sqlalchemy import delete, desc
from sqlmodel import select
from src.features.otp.models import OtpVerification
from sqlmodel.ext.asyncio.session import AsyncSession
from src.features.otp.request_schemas import CreateOtpRequestSchema
from datetime import datetime, UTC


class OtpRepository:

    async def save_generated_otp(self, otp_schema: CreateOtpRequestSchema, db: AsyncSession):
        statement = (
            delete(OtpVerification)
            .where(
                OtpVerification.user_id == otp_schema.user_id,
                OtpVerification.purpose == otp_schema.purpose
            )
        )
        await db.exec(statement=statement)
        await db.flush()
        otp_schema_dict = otp_schema.model_dump()
        otp_verification = OtpVerification(
            **otp_schema_dict
        )
        db.add(otp_verification)
        await db.flush()
        return otp_verification

    async def get_active_otp(self, email: str, purpose: str, db: AsyncSession) -> OtpVerification | None:
        now = datetime.now(UTC)
        statement = (
            select(OtpVerification)
            .where(
                OtpVerification.email == email,
                OtpVerification.purpose == purpose,
                OtpVerification.expires_at > now,
            )
            #.order_by(OtpVerification.created_at.desc())
            .order_by(desc(OtpVerification.created_at))
        )
        result = await db.exec(statement=statement)
        otp_record = result.first()
        if not otp_record:
            return None
        else:
            return otp_record


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
        statement = (
            delete(OtpVerification).where(
                OtpVerification.email == email,
                OtpVerification.purpose == purpose,
                OtpVerification.token_digest == code
            )
        )
        await db.exec(statement=statement)
        await db.flush()
        return True

    async def delete_expired_otp(self, email: str, purpose: str, db: AsyncSession) -> bool:
        statement = (
            delete(OtpVerification).where(
                OtpVerification.email == email,
                OtpVerification.purpose == purpose
            )
        )
        await db.exec(statement=statement)
        await db.flush()
        return True
