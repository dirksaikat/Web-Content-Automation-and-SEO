from src.features.auth.models import UserModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.features.auth.request_schema import CreateUserRequestSchema
from src.util.email_util import normalize_email
from src.core.security.password_util import hash_password
from src.util.date_util import utc_now

class TokenRepository:

    async def save_refresh_token(self, email: str, db: AsyncSession):
        normalized_email = normalize_email(email)
        statement = select(UserModel).where(UserModel.normalized_email == normalized_email)
        result = await self.session.exec(statement=statement)
        user = result.first()
        return user