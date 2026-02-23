from fastapi.security import HTTPBearer
from fastapi import Request, Depends
from src.core.security.token_util import decode_access_token
from src.infra.token_cache import TokenCache, get_token_cache
from .token_error import TokenError
from .token_util import _now


class AccessTokenBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(AccessTokenBearer, self).__init__(auto_error=auto_error)

    async def __call__(
            self,
            request: Request,
            token_cache: TokenCache = Depends(get_token_cache)
    ) -> dict | None:
        creds = await super(AccessTokenBearer, self).__call__(request)

        token = creds.credentials

        if not creds.scheme == "Bearer":
            raise TokenError.token_invalid()

        payload = decode_access_token(token)

        if not payload:
            # todo log here
            raise TokenError.token_invalid()

        user_id = payload.get("sub")
        if not user_id:
            # todo log here
            raise TokenError.token_invalid(message="Invalid user ID in token.")

        exp = payload.get("exp")
        if exp < _now():
            # todo log here token expired
            raise TokenError.token_expired()
        is_blacklisted = await token_cache.is_access_token_blacklisted(token_jti=payload.get("jti"))
        if is_blacklisted:
            # todo log here Blacklisted token.
            raise TokenError.token_invalid("Blacklisted token.")

        return payload
