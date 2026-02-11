from .models import User
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from .schemas import CreateUserRequestSchema
from src.util.email_util import normalize_email
from src.util.password_util import hash_password


class UserService:

    async def get_user_by_email(self, email: str, session: AsyncSession):
        normalized_email = normalize_email(email)
        statement = select(User).where(User.normalized_email == normalized_email)
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
        new_user.password_hash = hash_password(user_data_dict["password"])
        new_user.normalized_email = normalize_email(user_data.email)
        session.add(new_user)
        await session.commit()
        return new_user

    async def update_user(self, user: User, session: AsyncSession, **kwargs) -> User | None:
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await session.commit()
        return user
