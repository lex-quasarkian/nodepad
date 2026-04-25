from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from edwh_uuid7 import uuid7
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    hashed_password: Mapped[str]
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    lists: Mapped[list[NodeList]] = relationship(
        back_populates="owner", cascade="all, delete"
    )


if TYPE_CHECKING:
    from .lists import NodeList
