from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import Relationship
from sqlalchemy.sql import text
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)


class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    email: str = Field(sa_column=Column(String(255), nullable=False))
    normalized_email: str = Field(sa_column=Column(String(255), nullable=False))
    first_name: str
    last_name: str
    password_hash: str = Field(exclude=True)
    is_verified: bool = False
    is_active: bool = Field(sa_column=Column(Boolean, nullable=False, server_default="true"))

    # Account locking
    failed_login_attempts: int = Field(sa_column=Column(Integer, nullable=False, server_default="0"))
    account_locked_until: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    last_failed_login: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    refresh_tokens: List["RefreshTokenModel"] = Relationship(back_populates="user", sa_relationship_kwargs={
        "cascade": "all, delete-orphan"
    })

    def __repr__(self):
        return f"<User {self.username}>"


class RefreshTokenModel(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid.uuid4))
    token_hash: str = Field(sa_column=Column(String(64), nullable=False, unique=True))
    user_id: uuid.UUID = Field(default=None,
                               sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    device_id: str = Field(sa_column=Column(String(255), nullable=True))
    is_revoked: bool = Field(sa_column=Column(Boolean, nullable=False, server_default="false"))
    revoked_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP, nullable=True))
    expires_at: datetime = Field(sa_column=Column(TIMESTAMP, nullable=False, index=True))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    # Relationship
    user: Optional["UserModel"] = Relationship(back_populates="refresh_tokens")
