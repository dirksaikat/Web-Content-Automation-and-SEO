from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import String, Boolean
import uuid
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: uuid.UUID = Field(
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
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"<User {self.username}>"
