import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from edwh_uuid7 import uuid7
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .users import User


# Shared properties
class NodeListBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on list creation
class NodeListCreate(NodeListBase):
    pass


# Properties to receive on list update
class NodeListUpdate(NodeListBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)


# Database model, database table inferred from class name
class NodeList(NodeListBase):
    id: uuid.UUID = Field(default_factory=uuid7)
    created_at: datetime | None = Field()
    owner_id: uuid.UUID
    owner: Optional["User"]


# Properties to return via API, id is always required
class NodeListPublic(NodeListBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class NodeListsPublic(BaseModel):
    data: list[NodeListPublic]
    count: int


class NodeBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str | None = Field(default=None, max_length=255)


class Node(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    list_id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    position: Decimal
    created_at: datetime
    updated_at: datetime

    parent: list[uuid.UUID]
    children: list[uuid.UUID] | None = None
