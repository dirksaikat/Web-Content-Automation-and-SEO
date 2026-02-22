
from src.features.auth.user_repository import UserRepository
from src.features.auth.token_repository import TokenRepository


async def provide_user_service() -> UserRepository:
    return UserRepository()


async def provide_token_repository() -> TokenRepository:
    return TokenRepository()

get_user_repository = provide_user_service

get_token_repository = provide_token_repository
