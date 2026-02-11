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
    Enum as SAEnum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import  Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import LeakTag

class Qualification(Base):
    __tablename__ = "qualifications"

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

    diagnosis_tag: Mapped[Optional[LeakTag]] = mapped_column(SAEnum(LeakTag, name="leak_tag_enum"))
    one_sentence_summary: Mapped[Optional[str]] = mapped_column(Text)

    score: Mapped[Optional[int]] = mapped_column(Integer)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(64))  # book / park / not-fit / transfer
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    call: Mapped["Call"] = relationship(back_populates="qualifications")


