from src.features.auth.models import UserModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.features.auth.request_schema import CreateUserRequestSchema
from src.util.email_util import normalize_email
from src.core.security.password_util import hash_password
from src.util.date_util import utc_now
from .models import RefreshTokenModel
import uuid
from datetime import datetime
from sqlalchemy import and_, select, update


class TokenRepository:

    async def save_refresh_token(
            self,
            token_hash: str,
            token_expiry: int,
            user_id: str | None,
            device_id: str | None,
            db: AsyncSession) -> RefreshTokenModel:
        token = RefreshTokenModel(
            token_hash=token_hash,
            user_id=user_id,
            device_id=device_id,
            expires_at=datetime.fromtimestamp(token_expiry),
            is_revoked=False,
        )
        db.add(token)
        await db.flush()
        return token

    async def get_refresh_token(self, token_hash: str, db: AsyncSession) -> RefreshTokenModel | None:
        result = await db.execute(select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash))
        return result.scalars().first()

    async def revoke_refresh_token(self, token_hash: str, db: AsyncSession) -> bool:
        token = await self.get_refresh_token(token_hash=token_hash, db=db)
        if not token:
            return False
        token.is_revoked = True
        token.revoked_at = utc_now()
        await db.flush()
        return True

    async def revoke_all_user_tokens(self, user_id: str, db: AsyncSession) -> int:
        result = await db.execute(
            update(RefreshTokenModel)
            .where(and_(RefreshTokenModel.user_id == user_id, RefreshTokenModel.is_revoked.is_(False)))
            .values(is_revoked=True, revoked_at=utc_now())
        )

        await db.flush()
        count = result.rowcount or 0

        return count
