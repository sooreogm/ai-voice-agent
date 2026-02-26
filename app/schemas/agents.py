from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import UseCase


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    use_case: UseCase = UseCase.lead_qualification
    prompt: str | None = None
    first_message: str | None = None
    model_provider: str | None = None
    model: str | None = None
    model_temperature: float | None = None
    voice_provider: str | None = None
    voice_id: str | None = None
    cal_com_api_key: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    use_case: UseCase | None = None
    prompt: str | None = None
    first_message: str | None = None
    model_provider: str | None = None
    model: str | None = None
    model_temperature: float | None = None
    voice_provider: str | None = None
    voice_id: str | None = None
    cal_com_api_key: str | None = None


class AgentOut(BaseModel):
    id: str
    organization_id: str
    name: str
    use_case: str
    prompt: str | None
    first_message: str | None
    model_provider: str | None
    model: str | None
    voice_provider: str | None
    voice_id: str | None
    vapi_assistant_id: str | None
    cal_com_event_type_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
