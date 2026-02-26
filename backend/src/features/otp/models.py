from sqlmodel import SQLModel, Field
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    String,
    DateTime
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
    user_id: uuid.UUID = Field(sa_column=Column(default=None, foreign_key="users.id", nullable=False))
    token_digest: str = Field(sa_column=Column(max_length=128, unique=True, index=True, nullable=False))
    purpose: str = Field(sa_column=Column(default="verify", max_length=32, nullable=False))
    #expires_at: datetime = Field(sa_column=Column(nullable=False))
    #created_at: datetime = Field(sa_column=Column(default=datetime.now(UTC), nullable=False))

    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    def is_expired(self) -> bool:
        return self.expires_at < datetime.now(UTC)
