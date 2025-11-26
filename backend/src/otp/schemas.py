from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class CreateOtpSchema(BaseModel):
    user_uid: uuid.UUID
    code: str
    token_digest: str
    purpose: str
    salt: str
    expires_at: datetime


class AccountVerificationSchema(BaseModel):
    email: str
    otp: str
