from fastapi import APIRouter, Depends, status
from src.features.auth.user_repository import UserRepository
from src.features.auth.token_repository import TokenRepository
from src.features.otp.otp_repository import OtpRepository
from src.core.database.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.security.token_util import create_access_token, create_refresh_token, decode_refresh_token, hash_token
from src.core.security.access_token_bearer import AccessTokenBearer
from datetime import datetime
from src.features.otp.otp_utils import create_otp_schema
from src.mail.mail import send_mail_message
from src.infra.rate_limiter import RateLimitKey, get_rate_limiter
from src.util.email_util import validate_email
from src.core.security.password_util import validate_password_strength
from src.util.date_util import utc_now
from redis.asyncio import Redis
from src.features.auth.repositories_di import get_user_repository, get_token_repository
import time
from src.infra.redis_client import get_redis
from src.features.auth.auth_error import AuthError
from src.core.security.token_error import TokenError
from src.core.security.token_util import _now
from src.features.auth.request_schema import (
    UserSchema,
    CreateUserRequestSchema,
    LoginRequestSchema,
    RefreshAccessTokenRequest,
    LogoutRequest
)
from src.features.auth.response_schema import (
    CreateUserResponseSchema,
    LoginResponse,
    RefreshTokenResponse,
    LogoutResponse
)
from src.core.security.password_util import verify_password
from src.infra.token_cache import TokenCache, get_token_cache


auth_router = APIRouter()
otp_service = OtpRepository()
REFRESH_TOKEN_EXPIRY = 2

auth_rate_limiter = get_rate_limiter(
    limit=3,
    window_seconds=60,
    key_type=RateLimitKey.IP,
    block_seconds=3600
)


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_account(
        user_data: CreateUserRequestSchema,
        user_repository: UserRepository = Depends(get_user_repository),
        db: AsyncSession = Depends(get_session),
        redis: Redis = Depends(get_redis),
        _: None = Depends(auth_rate_limiter),
) -> CreateUserResponseSchema:
    email_validation = await validate_email(user_data.email)
    if not email_validation["valid"]:
        raise AuthError.invalid_email(errors=email_validation["errors"])

    pwd_validation = validate_password_strength(user_data.password, user_data.confirm_password)

    if not pwd_validation["valid"]:
        raise AuthError.invalid_password(errors=pwd_validation["errors"])

    lock_key = f"register_lock:{user_data.email}"
    lock = redis.lock(lock_key, timeout=10)

    try:
        acquired = await lock.acquire(blocking=True, blocking_timeout=5)

        if not acquired:
            raise AuthError.rate_limited(message="Registration in progress. Please try again.")

        user_exists = await user_repository.user_exists(email=user_data.email, db=db)

        if user_exists:
            raise AuthError.email_already_registered()

        new_user = await user_repository.create_user(user_data=user_data, db=db)

        otp_schema = create_otp_schema(email=user_data.email, user_id=new_user.id, purpose="account_verification")
        await otp_service.save_generated_otp(otp_schema=otp_schema, db=db)

        await db.commit()

        html = f"<h1>Your otp is {otp_schema.code} </h1>"
        await send_mail_message(
            recipients=[new_user.email],
            subject="OTP Verification",
            body=html
        )

        return CreateUserResponseSchema(
            message="Registration successful! Please check your email to verify your account.",
            user=UserSchema.model_validate(new_user),
            email_sent=True,
        )

    except Exception as e:
        await db.rollback()
        raise
    finally:
        await lock.release()


@auth_router.post("/login")
async def login_user(
        login_data: LoginRequestSchema,
        db: AsyncSession = Depends(get_session),
        token_cache: TokenCache = Depends(get_token_cache),
        user_repository: UserRepository = Depends(get_user_repository),
        token_repository: TokenRepository = Depends(get_token_repository),
        _: None = Depends(auth_rate_limiter),
) -> LoginResponse:
    email = login_data.email
    password = login_data.password

    user = await user_repository.get_user_by_email(email=email, db=db)

    if not user:
        raise AuthError.invalid_credentials()

    if user.account_locked_until:
        if user.account_locked_until > utc_now():
            minutes_left = int((user.account_locked_until - utc_now()).total_seconds() / 60)
            raise AuthError.account_locked(minutes_remaining=minutes_left)
        else:
            await user_repository.reset_account_lock(user=user, db=db)

    is_valid_password = verify_password(password=password, password_hash=user.password_hash)

    if not is_valid_password:
        await user_repository.increment_failed_login_attempt(user=user, db=db)
        raise AuthError.invalid_credentials()

    if not user.is_verified:
        raise AuthError.account_not_verified()

    if not user.is_active:
        raise AuthError.account_inactive()

    await user_repository.reset_account_lock(user=user, db=db)

    access_token, access_exp = create_access_token(str(user.id), role="user", device_id="234")
    refresh_token, refresh_hash, refresh_exp = create_refresh_token(str(user.id), device_id="234")
    await token_repository.save_refresh_token(
        token_hash=refresh_hash,
        token_expiry=refresh_exp,
        user_id=str(user.id),
        device_id=None,
        db=db
    )

    await token_cache.clear_user_access_token_blacklist(str(user.id))
    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=access_exp,
        user=UserSchema.model_validate(user)
    )


@auth_router.post("/token-refresh")
async def refresh_access_token(
        data: RefreshAccessTokenRequest,
        db: AsyncSession = Depends(get_session),
        token_cache: TokenCache = Depends(get_token_cache),
        user_repository: UserRepository = Depends(get_user_repository),
        token_repository: TokenRepository = Depends(get_token_repository),
) -> RefreshTokenResponse:

    refresh_token = data.refresh_token
    payload = decode_refresh_token(token=refresh_token)

    if not payload:
        # todo log here
        raise TokenError.token_invalid()

    user_id = payload.get("sub")
    if not user_id:
        raise TokenError.token_invalid(message="Invalid user ID in token.")

    token_hash = hash_token(token=refresh_token)
    stored_token = await token_repository.get_refresh_token(token_hash=token_hash, db=db)

    if not stored_token:
        raise TokenError.token_invalid()

    # Check if revoked (possible reuse attack) or expired
    if stored_token.is_revoked or stored_token.expires_at <= datetime.now():
        await token_repository.revoke_all_user_tokens(user_id=user_id, db=db)
        await token_cache.revoke_all_user_tokens(str(user_id))
        raise TokenError.token_invalid(message="Token has been revoked. All sessions terminated for security.")

    user = await user_repository.get_user_by_id(user_id=str(user_id), db=db)

    if not user:
        raise AuthError.user_not_found()

    if not user.is_active:
        raise AuthError.account_inactive()

    await token_repository.revoke_refresh_token(token_hash=token_hash, db=db)
    await token_cache.revoke_token(token_hash)

    access_token, access_exp = create_access_token(str(user.id), role="user", device_id="234")
    new_refresh_token, refresh_hash, refresh_exp = create_refresh_token(str(user.id), device_id="234")
    await token_repository.save_refresh_token(
        token_hash=refresh_hash,
        token_expiry=refresh_exp,
        user_id=str(user.id),
        device_id=None,
        db=db
    )
    await db.commit()

    return RefreshTokenResponse(
        access_token=access_token, refresh_token=new_refresh_token, expires_at=access_exp
    )


@auth_router.post("/logout")
async def revoke_token(
    logout_request: LogoutRequest,
    payload: dict = Depends(AccessTokenBearer()),
    token_cache: TokenCache = Depends(get_token_cache),
    db: AsyncSession = Depends(get_session),
    token_repository: TokenRepository = Depends(get_token_repository),
) -> LogoutResponse:

    jti = payload.get("jti")
    exp = payload.get("exp")
    user_id = payload.get("sub")

    if not jti or not exp or not user_id:
        raise TokenError.token_invalid("Invalid token payload")

    if logout_request.logout_all_devices:
        await token_repository.revoke_all_user_tokens(user_id=user_id, db=db)
    else:
        refresh_payload = decode_refresh_token(token=logout_request.refresh_token)

        if not refresh_payload:
            raise TokenError.token_invalid("Refresh token is invalid.")

        if refresh_payload.get("sub") != user_id:
            raise TokenError.token_invalid("Token mismatch")

        refresh_exp = refresh_payload.get("exp")
        if refresh_exp < _now():
            raise TokenError.token_invalid("Refresh token expired.")

        refresh_token_hash = hash_token(token=logout_request.refresh_token)

        existing_hash = await token_repository.get_refresh_token(token_hash=refresh_token_hash, db=db)

        if not existing_hash:
            raise TokenError.token_invalid()

        if existing_hash.is_revoked:
            raise TokenError.token_invalid("Refresh token already revoked")

        await token_repository.revoke_refresh_token(token_hash=refresh_token_hash, db=db)

    await db.commit()

    ttl = max(0, exp - int(time.time()))
    await token_cache.blacklist_access_token(jti, ttl)

    return LogoutResponse(message="Logged out successfully")
