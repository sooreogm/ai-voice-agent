from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.organization import Organization  # noqa: F401

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import UseCase


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    use_case: Mapped[UseCase] = mapped_column(
        SAEnum(UseCase, name="use_case_enum"), nullable=False, server_default=UseCase.lead_qualification.value
    )
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    voice_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    voice_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    enabled_tool_names: Mapped[list | None] = mapped_column(JSON, nullable=True)  # override; else from use_case
    vapi_assistant_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    vapi_phone_number_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cal_com_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted in production
    cal_com_event_type_id: Mapped[int | None] = mapped_column(nullable=True)
    tool_api_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="agents")
