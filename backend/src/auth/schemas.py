from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class UserSchema(BaseModel):
    uid: uuid.UUID
    email: str
    first_name: str
    last_name: str
    password_hash: str = Field(exclude=True)
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class CreateUserRequestSchema(BaseModel):
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class LoginRequestSchema(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class CreateOtpSchema(BaseModel):
    user_uid: uuid.UUID
    code: str
    token_digest: str
    purpose: str
    salt: str
    expires_at: datetime


class CreateUserResponseSchema(BaseModel):
    message: str

