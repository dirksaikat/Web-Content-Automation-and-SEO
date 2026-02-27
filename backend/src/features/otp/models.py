from sqlmodel import SQLModel, Field
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.sql import func


class OtpVerification(SQLModel, table=True):
    __tablename__ = "otp_verification"
    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    email: str = Field(sa_column=Column(String(255), nullable=False))
    user_id: uuid.UUID = Field(sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), default=None, nullable=False))
    token_digest: str = Field(sa_column=Column(String(128), unique=True, index=True, nullable=False))
    purpose: str = Field(sa_column=Column(String(50), default="verify", nullable=False))

    resend_available_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    def is_expired(self) -> bool:
        return self.expires_at <= datetime.now(UTC)
