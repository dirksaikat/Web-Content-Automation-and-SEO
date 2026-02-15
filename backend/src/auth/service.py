from datetime import timedelta

from .models import User
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .schemas import CreateUserRequestSchema
from src.util.email_util import normalize_email
from src.core.security.password_util import hash_password
from src.util.date_util import utc_now


class UserService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str):
        normalized_email = normalize_email(email)
        statement = select(User).where(User.normalized_email == normalized_email)
        result = await self.session.exec(statement=statement)
        user = result.first()
        return user

    async def user_exists(self, email: str):
        user = await self.get_user_by_email(email)
        return user is not None

    async def create_user(self, user_data: CreateUserRequestSchema):
        user_data_dict = user_data.model_dump()
        new_user = User(
            **user_data_dict
        )
        new_user.password_hash = hash_password(user_data_dict["password"])
        new_user.normalized_email = normalize_email(user_data.email)
        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def update_user(self, user: User, **kwargs) -> User | None:
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.session.commit()
        return user

    async def reset_account_lock(self, user: User):
        user.account_locked_until = None
        user.failed_login_attempts = 0
        await self.session.commit()

    async def increment_failed_login_attempt(self, user: User):
        user.failed_login_attempts += 1
        user.last_failed_login = utc_now()
        # Lock account if max attempts reached
        if user.failed_login_attempts >= 3:
            user.account_locked_until = utc_now() + timedelta(minutes=5)
        await self.session.commit()

