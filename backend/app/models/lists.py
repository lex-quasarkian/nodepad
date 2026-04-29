from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from edwh_uuid7 import uuid7
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import Ltree, LtreeType

from app.models import Base

if TYPE_CHECKING:
    from .users import User


class NodeList(Base):
    __tablename__ = "nodelist"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    owner: Mapped[User | None] = relationship(back_populates="lists")
    nodes: Mapped[list[Node]] = relationship(
        back_populates="nodelist",
        cascade="all, delete-orphan",
        order_by="cast(Node.path, String), Node.position",
    )


class Node(Base):
    __tablename__ = "node"

    __table_args__ = (
        CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="ck_node_parent_not_self",
        ),
        Index(
            "idx_nodes_list_parent_pos",
            "nodelist_id",
            "parent_id",
            "position",
        ),
        Index("idx_node_path_gist", "path", postgresql_using="gist"),
        Index("idx_node_level", "level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    nodelist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("nodelist.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("node.id", ondelete="CASCADE"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[Decimal] = mapped_column(
        Numeric(30, 15),
        nullable=False,
    )
    path: Mapped[Ltree] = mapped_column(LtreeType, nullable=False)
    level: Mapped[int] = mapped_column(nullable=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # relationships
    nodelist: Mapped[NodeList] = relationship(back_populates="nodes")
    parent: Mapped[Node | None] = relationship(
        back_populates="children",
        remote_side="Node.id",
    )

    children: Mapped[list[Node]] = relationship(
        back_populates="parent", order_by="Node.position"
    )
