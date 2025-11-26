from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime


class OtpVerification(SQLModel, table=True):
    __tablename__ = "otp_verification"
    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    user_uid: uuid.UUID = Field(default=None, foreign_key="users.uid", nullable=False)
    token_digest: str = Field(max_length=128, unique=True, index=True, nullable=False)
    purpose: str = Field(default="verify", max_length=32, nullable=False)
    salt: str = Field(max_length=64, nullable=True)
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
