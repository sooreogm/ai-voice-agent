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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import  PrimaryIntent, ResponseSpeed



class FitCheck(Base):
    __tablename__ = "fit_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
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

    business_offer: Mapped[Optional[str]] = mapped_column(Text)

    lead_sources: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))  # e.g. ["google", "instagram", ...]
    weekly_enquiries: Mapped[Optional[str]] = mapped_column(String(64))  # number or band text

    response_speed: Mapped[Optional[ResponseSpeed]] = mapped_column(
        SAEnum(ResponseSpeed, name="response_speed_enum")
    )

    booking_method: Mapped[Optional[str]] = mapped_column(Text)  # DMs/booking link/tool
    has_followup_system: Mapped[Optional[bool]] = mapped_column(Boolean)
    capacity_next_weeks: Mapped[Optional[bool]] = mapped_column(Boolean)

    primary_intent: Mapped[Optional[PrimaryIntent]] = mapped_column(
        SAEnum(PrimaryIntent, name="primary_intent_enum")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    call: Mapped["Call"] = relationship(back_populates="fit_checks")


