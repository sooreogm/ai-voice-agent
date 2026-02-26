from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CallListItem(BaseModel):
    id: str
    vapi_call_id: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_sec: int | None
    outcome_tag: str | None
    recording_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadListItem(BaseModel):
    id: str
    name: str | None
    business_name: str | None
    phone: str | None
    email: str | None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class BookingListItem(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
    status: str
    meeting_link: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ToolCallItem(BaseModel):
    id: str
    tool_name: str
    request_json: dict | None
    response_json: dict | None
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CallDetail(BaseModel):
    id: str
    vapi_call_id: str
    organization_id: str
    agent_id: str | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_sec: int | None
    transcript: str | None
    recording_url: str | None
    outcome_tag: str | None
    outcome_note: str | None
    created_at: datetime
    lead: LeadListItem | None = None
    tool_calls: list[ToolCallItem] = []

    class Config:
        from_attributes = True
