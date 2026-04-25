import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from edwh_uuid7 import uuid7
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .users import User


class NodeBase(BaseModel):
    content: str | None = Field(default=None, max_length=255)


class Node(NodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nodelist_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    content: str
    position: Decimal
    created_at: datetime
    updated_at: datetime


class NodeCreate(NodeBase):
    content: str = Field(max_length=255)
    position: Decimal | None = Field(default=None)
    parent_id: uuid.UUID | None = Field(default=None)


# Shared properties
class NodeListBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    nodes: list[Node | None] = Field(default_factory=list)


# Properties to receive on list creation
class NodeListCreate(NodeListBase):
    nodes: list[NodeCreate | None] = Field(default_factory=list)


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
