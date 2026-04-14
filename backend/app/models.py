import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from edwh_uuid7 import uuid7
from pydantic import EmailStr
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Numeric, text
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    lists: list["List"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ListBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on list creation
class ListCreate(ListBase):
    pass


# Properties to receive on list update
class ListUpdate(ListBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class List(ListBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="lists")


# Properties to return via API, id is always required
class ListPublic(ListBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ListsPublic(SQLModel):
    data: list[ListPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class NodeBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    content: str | None = Field(default=None, max_length=255)


class Node(SQLModel, table=True):
    __tablename__ = "node"

    __table_args__ = (
        CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="ck_node_parent_not_self",
        ),
        Index(
            "idx_nodes_list_parent_pos",
            "list_id",
            "parent_id",
            "position",
        ),
    )

    id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            primary_key=True,
        )
    )

    list_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("list.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    parent_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("node.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    title: str = Field(nullable=False)

    position: Decimal = Field(
        sa_column=Column(
            Numeric(30, 15),
            nullable=False,
        )
    )

    created_at: datetime = Field(
        sa_column=Column(
            nullable=False,
            server_default=text("now()"),
        )
    )

    updated_at: datetime = Field(
        sa_column=Column(
            nullable=False,
            server_default=text("now()"),
        )
    )

    # relationships

    parent: Optional["Node"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Node.id"},
    )

    children: list["Node"] = Relationship(back_populates="parent")
