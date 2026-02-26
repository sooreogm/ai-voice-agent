from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.leads import Lead
    from app.models.fit_check import FitCheck
    from app.models.qualifications import Qualification
    from app.models.bookings import Booking
    from app.models.handoffs import Handoff
    from app.models.tool_call import ToolCall
    from app.models.organization import Organization
    from app.models.agent import Agent

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum as SAEnum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OutcomeTag

class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    vapi_call_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    lead_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer)

    recording_url: Mapped[Optional[str]] = mapped_column(Text)
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)

    outcome_tag: Mapped[Optional[OutcomeTag]] = mapped_column(SAEnum(OutcomeTag, name="outcome_tag_enum"))
    outcome_note: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    
    knowledge_version: Mapped[Optional[str]] = mapped_column(String(255))
    assistant_version: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="calls")
    fit_checks: Mapped[List["FitCheck"]] = relationship(back_populates="call", cascade="all, delete-orphan")
    qualifications: Mapped[List["Qualification"]] = relationship(back_populates="call", cascade="all, delete-orphan")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="call", cascade="all, delete-orphan")
    handoffs: Mapped[List["Handoff"]] = relationship(back_populates="call", cascade="all, delete-orphan")
    tool_calls: Mapped[List["ToolCall"]] = relationship(back_populates="call", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_calls_lead_id", "lead_id"),
        Index("idx_calls_org_vapi", "organization_id", "vapi_call_id"),
        UniqueConstraint("organization_id", "vapi_call_id", name="uq_calls_org_vapi_call_id"),
    )

