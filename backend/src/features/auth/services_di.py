from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.auth.user_repository import UserRepository
from src.features.auth.token_repository import TokenRepository
from src.core.database.main import get_session


async def provide_user_service() -> UserRepository:
    return UserRepository()


async def provide_token_repository(db: Annotated[AsyncSession, Depends(get_session)]) -> TokenRepository:
    return TokenRepository()

get_user_repository = provide_user_service
get_token_repository = provide_token_repository
