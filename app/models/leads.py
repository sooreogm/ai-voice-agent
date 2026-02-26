from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.calls import Call
    from app.models.bookings import Booking
    from app.models.handoffs import Handoff

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

# -------------------------
# Core Models
# -------------------------
class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[Optional[str]] = mapped_column(String(255))
    business_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[Optional[str]] = mapped_column(String(120))

    phone: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    industry: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(255))

    source: Mapped[str] = mapped_column(String(64), nullable=False, server_default="inbound_call")

    # Relationships
    calls: Mapped[List["Call"]] = relationship(back_populates="lead", cascade="save-update", passive_deletes=True)
    bookings: Mapped[List["Booking"]] = relationship(back_populates="lead", cascade="save-update", passive_deletes=True)
    handoffs: Mapped[List["Handoff"]] = relationship(back_populates="lead", cascade="save-update", passive_deletes=True)

    __table_args__ = (UniqueConstraint("organization_id", "phone", name="uq_leads_org_phone"),)
