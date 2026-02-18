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
    email: str
    user_id: uuid.UUID = Field(default=None, foreign_key="users.id", nullable=False)
    token_digest: str = Field(max_length=128, unique=True, index=True, nullable=False)
    purpose: str = Field(default="verify", max_length=32, nullable=False)
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    def is_expired(self) -> bool:
        return self.expires_at < datetime.utcnow()
