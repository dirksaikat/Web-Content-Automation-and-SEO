from .models import User
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from .schemas import CreateUserRequestSchema
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

    async def update_user(self, user: User, session: AsyncSession, **kwargs) -> User | None:
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await session.commit()
        return user
