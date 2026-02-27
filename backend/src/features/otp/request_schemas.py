from pydantic import BaseModel
import uuid
from datetime import datetime


class CreateOtpRequestSchema(BaseModel):
    email: str
    user_id: uuid.UUID
    code: str
    token_digest: str
    purpose: str
    resend_available_at: datetime
    expires_at: datetime


class VerifyAccountRequestSchema(BaseModel):
    email: str
    otp: str


class ResendAccountVerificationOptRequestSchema(BaseModel):
    email: str



