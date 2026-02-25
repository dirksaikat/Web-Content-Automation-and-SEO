import hashlib
import random
from datetime import datetime, timedelta
from src.features.otp.request_schemas import CreateOtpRequestSchema
import uuid


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def create_otp_schema(email: str, user_id: uuid.UUID, purpose: str, ttl_minutes=10) -> CreateOtpRequestSchema:
    code = f"{random.randint(100000, 999999)}"
    digest = hash_otp(code)
    return CreateOtpRequestSchema(
        email=email,
        user_id=user_id,
        code=code,
        purpose=purpose,
        token_digest=digest,
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes)
    )


def verify_code_matches(code: str, stored_digest: str):
    return hash_otp(code=code) == stored_digest
