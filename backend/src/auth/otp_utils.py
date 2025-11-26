import hashlib
import os
import random
from datetime import datetime, timedelta
from .schemas import CreateOtpSchema
import uuid


def create_otp_schema(user_uid: uuid.UUID, purpose: str, ttl_minutes=10) -> CreateOtpSchema:
    code = f"{random.randint(100000, 999999)}"
    salt = os.urandom(16).hex()
    digest = hashlib.sha256((salt + code).encode()).hexdigest()
    return CreateOtpSchema(
        user_uid=user_uid,
        code=code,
        salt=salt,
        purpose=purpose,
        token_digest=digest,
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes)
    )


def verify_code_matches(input_code, salt, stored_digest):
    return hashlib.sha256((salt + input_code).encode()).hexdigest() == stored_digest
