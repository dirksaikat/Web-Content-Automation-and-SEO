from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from .schemas import CreateUserRequestSchema, UserSchema, LoginRequestSchema, CreateUserResponseSchema
from .service import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from .utils import create_access_token, decode_token, verify_password
from .dependencies import RefreshTokenBearer, AccessTokenBearer
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse
from src.errors.errors import UserAlreadyExists, InvalidCredentials, InvalidToken
from .otp_utils import create_otp_schema

auth_router = APIRouter()
user_service = UserService()
REFRESH_TOKEN_EXPIRY = 2


@auth_router.post("/signup", response_model=CreateUserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user_account(user_data: CreateUserRequestSchema, session: AsyncSession = Depends(get_session)):
    email = user_data.email
    user_exists = await user_service.user_exists(email=email, session=session)
    if user_exists:
        raise UserAlreadyExists()
    new_user = await user_service.create_user(user_data=user_data, session=session)
    otp_schema = create_otp_schema(user_uid=new_user.uid, purpose="otp_verification")
    await user_service.save_generated_otp(otp_schema=otp_schema, session=session)

    return {
        "message": "An otp was sent to the registered email.",
    }


@auth_router.post("/login")
async def login_user(login_data: LoginRequestSchema, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email=email, session=session)

    if user is not None:
        is_valid_password = verify_password(password=password, password_hash=user.password_hash)
        if is_valid_password:
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