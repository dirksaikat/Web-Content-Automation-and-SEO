from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class CreateOtpSchema(BaseModel):
    email: str
    user_id: uuid.UUID
    code: str
    token_digest: str
    purpose: str
    expires_at: datetime


class AccountVerificationSchema(BaseModel):
    email: str
    otp: str


class EmailVerificationResponseSchema(BaseModel):
    message: str = Field(..., description="Success message")
    email_verified: bool = Field(default=True, description="Email verification status")

    model_config = {
        "json_schema_extra": {"examples": [{"message": "Email verified successfully.", "email_verified": True}]}
    }