from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.calls import Call

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    Enum as SAEnum,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=True
    )
    call_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    tool_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    request_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    response_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    success: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    error: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    call: Mapped[Optional["Call"]] = relationship(back_populates="tool_calls")