from .models import OtpVerification
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import CreateOtpSchema


class OtpService:

    async def save_generated_otp(self, otp_schema: CreateOtpSchema, session: AsyncSession):
        otp_schema_dict = otp_schema.model_dump()
        otp_verification = OtpVerification(
            **otp_schema_dict
        )
        session.add(otp_verification)
        await session.commit()
        return otp_verification
