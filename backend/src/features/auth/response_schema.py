from pydantic import BaseModel, Field
from .request_schema import UserSchema


class CreateUserResponseSchema(BaseModel):
    message: str = Field(
        default="Registration successful! Please check your email to verify your account.",
        description="Success message",
    )
    user: UserSchema = Field(..., description="Registered user info")
    email_sent: bool = Field(default=True, description="Whether verification email was sent")


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_at: int = Field(..., description="Unix timestamp when access token expires")
    user: UserSchema = Field(..., description="Authenticated user info")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "expires_at": 1702000000,
                    "user": {
                        "id": "abc123",
                        "email": "user@example.com",
                        "role": "user",
                        "is_active": True,
                        "email_verified": True,
                    },
                }
            ]
        }
    }
