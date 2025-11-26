from .models import User, OtpVerification
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from .schemas import CreateUserRequestSchema, CreateOtpSchema
from .utils import generate_password_hash


class UserService:

    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement=statement)
        user = result.first()
        return user

    async def user_exists(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        return user is not None

    async def create_user(self, user_data: CreateUserRequestSchema, session: AsyncSession):
        user_data_dict = user_data.model_dump()
        new_user = User(
            **user_data_dict
        )
        new_user.password_hash = generate_password_hash(user_data_dict["password"])
        session.add(new_user)
        await session.commit()
        return new_user

    async def save_generated_otp(self, otp_schema: CreateOtpSchema, session: AsyncSession):
        otp_schema_dict = otp_schema.model_dump()
        otp_verification = OtpVerification(
            **otp_schema_dict
        )
        session.add(otp_verification)
        await session.commit()
        return otp_verification
