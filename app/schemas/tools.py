from typing import Optional, List, Literal

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class UpsertLeadRequest(BaseModel):
    call_id: Optional[str] = Field(default=None, description="Vapi call id")
    name: Optional[str] = None
    business_name: Optional[str] = None 
    role: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    source: Literal["inbound_call"] = "inbound_call"
    notes: Optional[str] = None


class UpsertLeadResponse(BaseModel):
    lead_id: str
    status: Literal["created", "updated"]


class FitCheckSaveRequest(BaseModel):
    call_id: str
    lead_id: UUID

    business_offer: Optional[str] = None
    lead_sources: Optional[List[str]] = None
    weekly_enquiries: Optional[str] = None
    response_speed: Optional[Literal["under_10_min", "within_hour", "same_day", "later", "unknown"]] = None
    booking_method: Optional[str] = None
    has_followup_system: Optional[bool] = None
    capacity_next_weeks: Optional[bool] = None
    primary_intent: Optional[Literal["more_enquiries", "enquiries_not_converting", "stop_going_cold", "unknown"]] = None


class FitCheckSaveResponse(BaseModel):
    fit_check_id: str


class QualifyRequest(BaseModel):
    call_id: str
    lead_id: UUID
    diagnosis_tag: Optional[
        Literal[
            "#leak-speed",
            "#leak-fragmentation",
            "#leak-followup",
            "#leak-booking",
            "#leak-traffic",
        ]
    ] = None
    one_sentence_summary: Optional[str] = None
    notes: Optional[str] = None


class QualifyResponse(BaseModel):
    qualification_id: str
    score: int
    recommended_action: Literal["book", "park", "not-fit", "transfer"]


class AvailabilityResponse(BaseModel):
    timezone: str = "Europe/London"
    slots: List[str]


class BookAuditRequest(BaseModel):
    call_id: str
    lead_id: str
    start_time_iso: str
    timezone: str = "Europe/London"
    duration_minutes: Literal[15] = 15
    attendee_email: EmailStr
    attendee_name: Optional[str] = None
    attendee_phone: Optional[str] = None
    notes: Optional[str] = None


class BookAuditResponse(BaseModel):
    booking_id: str
    status: Literal["booked"] = "booked"
    calendar_event_id: Optional[str] = None
    meeting_link: Optional[str] = None


class OutcomeLogRequest(BaseModel):
    call_id: str
    lead_id: Optional[str] = None
    outcome_tag: Literal[
        "#audit-booked",
        "#requested-info",
        "#callback-scheduled",
        "#parked",
        "#not-a-fit",
        "#no-answer",
    ]
    note: Optional[str] = None


class OutcomeLogResponse(BaseModel):
    ok: bool = True


class HandoffRequest(BaseModel):
    call_id: str
    lead_id: str
    reason: str
    target_phone: Optional[str] = None


class HandoffResponse(BaseModel):
    handoff_id: str
    status: Literal["queued"] = "queued"
    instruction: str = "I’m connecting you now. One moment please."