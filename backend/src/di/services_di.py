from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.service import UserService
from src.core.database.main import get_session


async def provide_user_service(db: Annotated[AsyncSession, Depends(get_session)]) -> UserService:
    return UserService(db)


get_user_service = provide_user_service
