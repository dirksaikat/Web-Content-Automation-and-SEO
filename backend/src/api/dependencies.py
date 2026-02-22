from fastapi.security import HTTPBearer
from fastapi import Request, Depends
from src.core.security.token_util import decode_access_token
from src.core.database.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.features.auth.user_repository import UserRepository
from src.features.auth.services_di import get_user_repository
from src.errors.errors import InvalidToken, AccessTokenRequired


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(TokenBearer, self).__init__(auto_error=auto_error)

    # Todo ask issue about return type
    #async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
    async def __call__(self, request: Request) -> dict | None:
        creds = await super(TokenBearer, self).__call__(request)

        token = creds.credentials

        if not creds.scheme == "Bearer":
            raise InvalidToken()

        if not self.is_valid_token(token):
            raise InvalidToken()

        token_data = decode_access_token(token)

        # if await token_in_blocklist(token_data['jti']):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail={
        #             "error": "This token is invalid or revoked",
        #             "resolution": "Please get new token."
        #         }
        #     )

        self.verify_token_data(token_data)

        return token_data

    def is_valid_token(self, jwt_token: str) -> bool:
        token_data = decode_access_token(jwt_token)
        return True if token_data is not None else False

    def verify_token_data(self, token_dict: dict):
        raise NotImplementedError("Override this method in child class")


class AccessTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict):
        if token_data and token_data["refresh"]:
            raise AccessTokenRequired()



async def get_current_user(
        token_details: dict = Depends(AccessTokenBearer()),
        session: AsyncSession = Depends(get_session),
        user_service: UserRepository = Depends(get_user_repository),
):
    user_email = token_details['user']['email']
    user = await user_service.get_user_by_email(email=user_email, session=session)
    return user

