from pydantic import BaseModel, Field

from .lists import (
    Node,
    NodeBase,
    NodeCreate,
    NodeListBase,
    NodeListCreate,
    NodeListPublic,
    NodeListsPublic,
    NodeListUpdate,
)
from .users import (
    PrivateUserCreate,
    UpdatePassword,
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)


# Generic message
class Message(BaseModel):
    message: str


# JSON payload containing access token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseModel):
    sub: str | None = None


class NewPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


__all__ = [
    "Node",
    "NodeBase",
    "NodeCreate",
    "NodeListBase",
    "NodeListCreate",
    "NodeListPublic",
    "NodeListsPublic",
    "NodeListUpdate",
    "PrivateUserCreate",
    "UpdatePassword",
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    "UserRegister",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    "Message",
    "Token",
    "TokenPayload",
    "NewPassword",
]
