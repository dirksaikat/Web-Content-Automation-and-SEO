from fastapi.security import HTTPBearer
from fastapi import Request, Depends
from src.core.database.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.features.auth.user_repository import UserRepository
from src.features.auth.repositories_di import get_user_repository

from src.core.security.access_token_bearer import AccessTokenBearer


async def get_current_user(
        token_details: dict = Depends(AccessTokenBearer()),
        db: AsyncSession = Depends(get_session),
        user_service: UserRepository = Depends(get_user_repository),
):
    user_email = token_details['user']['email']
    user = await user_service.get_user_by_email(email=user_email, db=db)
    return user

