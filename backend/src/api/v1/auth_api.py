from fastapi import APIRouter, Depends, status
from src.features.auth.user_repository import UserRepository
from src.otp.service import OtpService
from src.core.database.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.security.token_util import create_access_token, create_refresh_token
from src.api.dependencies import RefreshTokenBearer, AccessTokenBearer
from datetime import datetime
from fastapi.responses import JSONResponse
from src.errors.errors import InvalidToken
from src.otp.otp_utils import create_otp_schema
from src.mail.mail import send_mail_message
from src.infra.rate_limiter import RateLimitKey, get_rate_limiter
from src.util.email_util import validate_email
from src.core.security.password_util import validate_password_strength
from src.util.date_util import utc_now
from redis.asyncio import Redis
from src.features.auth.services_di import get_user_repository
from src.infra.redis_client import get_redis
from src.features.auth.auth_error import AuthError
from src.features.auth.request_schema import UserSchema, CreateUserRequestSchema, LoginRequestSchema
from src.features.auth.response_schema import CreateUserResponseSchema, LoginResponse
from src.core.security.password_util import verify_password

auth_router = APIRouter()
otp_service = OtpService()
REFRESH_TOKEN_EXPIRY = 2

register_rate_limiter = get_rate_limiter(
    limit=3,
    window_seconds=60,
    key_type=RateLimitKey.IP,
    block_seconds=300
)


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_account(
        user_data: CreateUserRequestSchema,
        user_service: UserRepository = Depends(get_user_repository),
        db: AsyncSession = Depends(get_session),
        redis: Redis = Depends(get_redis),
        _: None = Depends(register_rate_limiter),
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

        user_exists = await user_service.user_exists(email=user_data.email, db=db)

        if user_exists:
            raise AuthError.email_already_registered()

        new_user = await user_service.create_user(user_data=user_data, db=db)
        print("New user")
        print(new_user.id)
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
        user_service: UserRepository = Depends(get_user_repository),
) -> LoginResponse:
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email=email, db=db)

    if not user:
        raise AuthError.invalid_credentials()

    if user.account_locked_until:
        if user.account_locked_until > utc_now():
            minutes_left = int((user.account_locked_until - utc_now()).total_seconds() / 60)
            raise AuthError.account_locked(minutes_remaining=minutes_left)
        else:
            await user_service.reset_account_lock(user=user, db=db)

    is_valid_password = verify_password(password=password, password_hash=user.password_hash)

    if not is_valid_password:
        await user_service.increment_failed_login_attempt(user=user, db=db)
        raise AuthError.invalid_credentials()

    if not user.is_verified:
        raise AuthError.account_not_verified()

    if not user.is_active:
        raise AuthError.account_inactive()

    await user_service.reset_account_lock(user=user, db=db)

    access_token, access_exp = create_access_token(str(user.id), role="user", device_id="234")
    refresh_token, refresh_hash, refresh_exp = create_refresh_token(str(user.id), device_id="234")

    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=access_exp,
        user=UserSchema.model_validate(user)
    )


@auth_router.get("/refresh_token")
async def create_new_access_token(
        token_details: dict = Depends(RefreshTokenBearer())
):
    expiry_timestamp = token_details["exp"]
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(token_details["user"])
        return JSONResponse(
            content={
                "access_token": new_access_token
            }
        )
    raise InvalidToken()


@auth_router.post("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    #await add_jti_to_blocklist(jti=jti)
    return JSONResponse(
        content={
            "message": "Logged out successfully"
        },
        status_code=status.HTTP_200_OK
    )
