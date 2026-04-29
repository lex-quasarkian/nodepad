import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

LtreeStr = Annotated[str, BeforeValidator(str)]


if TYPE_CHECKING:
    pass


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
    updated_at: datetime | None = None
    path: LtreeStr
    level: int


class NodeCreate(NodeBase):
    id: uuid.UUID | None = Field(default=None)
    content: str = Field(max_length=255)
    position: Decimal | None = Field(default=None)
    parent_id: uuid.UUID | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)


# Shared properties
class NodeListBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    nodes: list[Node | None] = Field(default_factory=list)


# Properties to receive on list creation
class NodeListCreate(NodeListBase):
    nodes: list[NodeCreate | None] = Field(default_factory=list)


class NodeUpdate(NodeBase):
    id: uuid.UUID | None = Field(default=None)
    parent_id: uuid.UUID | None = Field(default=None)
    position: Decimal | None = Field(default=None)
    level: int | None = Field(default=None)


# Properties to receive on list update
class NodeListUpdate(NodeListBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    nodes: list[NodeUpdate | None] | None = Field(default=None)


# Properties to return via API, id is always required
class NodeListPublic(NodeListBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NodeListsPublic(BaseModel):
    data: list[NodeListPublic]
    count: int
