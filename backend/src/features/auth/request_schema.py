from pydantic import BaseModel, Field, ConfigDict, EmailStr
import uuid
from datetime import datetime


class UserSchema(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    password_hash: str = Field(exclude=True)
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CreateUserRequestSchema(BaseModel):
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)


class LoginRequestSchema(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class RefreshAccessTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
    logout_all_devices: bool = False


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    password: str
    confirm_password: str


