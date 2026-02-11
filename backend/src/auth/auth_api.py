from fastapi import APIRouter, Depends, status
from .service import UserService
from src.otp.service import OtpService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from .utils import create_access_token, verify_password
from .dependencies import RefreshTokenBearer, AccessTokenBearer
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse
from src.errors.errors import InvalidCredentials, InvalidToken, AccountNotVerified
from src.otp.otp_utils import create_otp_schema
from src.mail.mail import send_mail_message
from src.infra.rate_limiter import RateLimitKey, get_rate_limiter
from src.util.email_util import validate_email
from src.util.password_util import validate_password_strength, hash_password
from redis.asyncio import Redis
from src.infra.redis_client import get_redis
from src.errors.auth_error import AuthError
from .schemas import UserSchema, CreateUserResponseSchema, CreateUserRequestSchema, LoginRequestSchema

auth_router = APIRouter()
user_service = UserService()
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
        session: AsyncSession = Depends(get_session),
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

        user_exists = await user_service.user_exists(email=user_data.email, session=session)

        if user_exists:
            raise AuthError.email_already_registered()

        new_user = await user_service.create_user(user_data=user_data, session=session)
        otp_schema = create_otp_schema(email=user_data.email, user_uid=new_user.uid, purpose="account_verification")
        await otp_service.save_generated_otp(otp_schema=otp_schema, session=session)
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
        await session.rollback()
        raise
    finally:
        await lock.release()


@auth_router.post("/login")
async def login_user(login_data: LoginRequestSchema, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email=email, session=session)

    if user is not None:
        is_valid_password = verify_password(password=password, password_hash=user.password_hash)
        if is_valid_password:

            if not user.is_verified:
                raise AccountNotVerified()

            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid)
                }
            )

            refresh_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid)
                },
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )

            return JSONResponse(
                content={
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "email": user.email,
                        "uid": str(user.uid)
                    }
                }
            )
    raise InvalidCredentials()


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
