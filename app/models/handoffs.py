from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.calls import Call
    from app.models.leads import Lead

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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import HandoffStatus


class Handoff(Base):
    __tablename__ = "handoffs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lead_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    target_phone: Mapped[Optional[str]] = mapped_column(String(64))

    status: Mapped[HandoffStatus] = mapped_column(
        SAEnum(HandoffStatus, name="handoff_status_enum"),
        nullable=False,
        server_default=HandoffStatus.queued.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    call: Mapped["Call"] = relationship(back_populates="handoffs")
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="handoffs")


