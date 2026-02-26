from __future__ import annotations

from fastapi import APIRouter

from app.schemas.tools import (AvailabilityResponse, 
                                BookAuditRequest, BookAuditResponse, 
                                FitCheckSaveRequest, FitCheckSaveResponse, 
                                HandoffRequest, HandoffResponse, OutcomeLogRequest, 
                                OutcomeLogResponse, QualifyRequest, QualifyResponse, 
                                UpsertLeadRequest, UpsertLeadResponse
                            )
import uuid
from datetime import datetime, timedelta
from typing import Optional, Literal, Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_agent_from_key
from app.models import Agent
from app import models

router = APIRouter(prefix="/tools", tags=["Tools"])

# Helpers
# -------------------------
def get_or_create_call(
    db: Session,
    vapi_call_id: str,
    organization_id: uuid.UUID,
    agent_id: Optional[uuid.UUID],
) -> models.Call:
    call = (
        db.query(models.Call)
        .filter(
            models.Call.organization_id == organization_id,
            models.Call.vapi_call_id == vapi_call_id,
        )
        .first()
    )
    if call:
        return call
    call = models.Call(
        vapi_call_id=vapi_call_id,
        organization_id=organization_id,
        agent_id=agent_id,
    )
    db.add(call)
    db.flush()
    return call


def log_tool_call(
    db: Session,
    organization_id: uuid.UUID,
    call_id: Optional[uuid.UUID],
    tool_name: str,
    request_json: Dict[str, Any],
    response_json: Dict[str, Any],
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    db.add(
        models.ToolCall(
            organization_id=organization_id,
            call_id=call_id,
            tool_name=tool_name,
            request_json=request_json,
            response_json=response_json,
            success=success,
            error=error,
        )
    )


# Endpoints
# -------------------------
@router.post("/leads/upsert", response_model=UpsertLeadResponse)
def upsert_lead(
    payload: UpsertLeadRequest,
    agent: Agent = Depends(get_agent_from_key),
    db: Session = Depends(get_db),
) -> UpsertLeadResponse:
    org_id = agent.organization_id
    agent_id = agent.id
    vapi_call_id = payload.call_id
    call = get_or_create_call(db, vapi_call_id, org_id, agent_id) if vapi_call_id else None

    lead = (
        db.query(models.Lead)
        .filter(models.Lead.organization_id == org_id, models.Lead.phone == payload.phone)
        .first()
    )
    if lead:
        status = "updated"
    else:
        lead = models.Lead(organization_id=org_id, phone=payload.phone)
        db.add(lead)
        status = "created"

    for field in ["name", "business_name", "role", "email", "industry", "location", "source"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(lead, field, val)

    db.flush()

    if call and not call.lead_id:
        call.lead_id = lead.id

    resp = {"lead_id": str(lead.id), "status": status}
    log_tool_call(db, org_id, call.id if call else None, "upsertLead", payload.model_dump(mode="json"), resp)

    db.commit()
    return UpsertLeadResponse(**resp)  # pyright: ignore[reportArgumentType]


@router.post("/fit-check/save", response_model=FitCheckSaveResponse)
def save_fit_check(
    payload: FitCheckSaveRequest,
    agent: Agent = Depends(get_agent_from_key),
    db: Session = Depends(get_db),
) -> FitCheckSaveResponse:
    org_id = agent.organization_id
    call = get_or_create_call(db, payload.call_id, org_id, agent.id)

    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == payload.lead_id, models.Lead.organization_id == org_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not call.lead_id:
        call.lead_id = lead.id

    fit = models.FitCheck(
        organization_id=org_id,
        call_id=call.id,
        lead_id=lead.id,
        business_offer=payload.business_offer,
        lead_sources=payload.lead_sources,
        weekly_enquiries=payload.weekly_enquiries,
        response_speed=payload.response_speed,
        booking_method=payload.booking_method,
        has_followup_system=payload.has_followup_system,
        capacity_next_weeks=payload.capacity_next_weeks,
        primary_intent=payload.primary_intent,
    )
    db.add(fit)
    db.flush()

    resp = {"fit_check_id": str(fit.id)}
    log_tool_call(db, org_id, call.id, "saveFitCheck", payload.model_dump(mode="json"), resp)

    db.commit()
    return FitCheckSaveResponse(**resp)


@router.post("/qualification/score", response_model=QualifyResponse)
def qualify_and_tag(
    payload: QualifyRequest,
    agent: Agent = Depends(get_agent_from_key),
    db: Session = Depends(get_db),
) -> QualifyResponse:
    org_id = agent.organization_id
    call = get_or_create_call(db, payload.call_id, org_id, agent.id)

    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == payload.lead_id, models.Lead.organization_id == org_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not call.lead_id:
        call.lead_id = lead.id

    score = 50
    if payload.diagnosis_tag:
        score += 10
    if payload.one_sentence_summary:
        score += 10

    recommended_action: Literal["book", "park", "not-fit", "transfer"] = "book" if score >= 55 else "park"

    q = models.Qualification(
        organization_id=org_id,
        call_id=call.id,
        lead_id=lead.id,
        diagnosis_tag=payload.diagnosis_tag,
        one_sentence_summary=payload.one_sentence_summary,
        score=score,
        recommended_action=recommended_action,
        notes=payload.notes,
    )
    db.add(q)
    db.flush()

    resp = {"qualification_id": str(q.id), "score": score, "recommended_action": recommended_action}
    log_tool_call(db, org_id, call.id, "qualifyAndTag", payload.model_dump(mode="json"), resp)

    db.commit()
    return QualifyResponse(**resp)


# @router.get("/calendar/availability", response_model=AvailabilityResponse)
# def get_availability(
#     timezone: str = "Europe/London",
#     days_ahead: int = 7,
#     db: Session = Depends(get_db),
# ) -> AvailabilityResponse:
#     # Placeholder slots. Replace with Google Calendar free/busy later.
#     now = datetime.utcnow()
#     slots = []
#     for i in range(min(days_ahead, 7)):
#         day = now + timedelta(days=i)
#         slots.append(day.replace(hour=10, minute=0, second=0, microsecond=0).isoformat() + "Z")
#         slots.append(day.replace(hour=14, minute=0, second=0, microsecond=0).isoformat() + "Z")

#     resp = {"timezone": timezone, "slots": slots}
#     log_tool_call(db, None, "getAvailability", {"timezone": timezone, "days_ahead": days_ahead}, resp)
#     db.commit()
#     return AvailabilityResponse(**resp)


# @router.post("/calendar/book", response_model=BookAuditResponse)
# def book_audit(payload: BookAuditRequest, db: Session = Depends(get_db)) -> BookAuditResponse:
#     call = get_or_create_call(db, payload.call_id)

#     lead = db.query(models.Lead).filter(models.Lead.id == uuid.UUID(payload.lead_id)).first()
#     if not lead:
#         raise HTTPException(status_code=404, detail="Lead not found")

#     if not call.lead_id:
#         call.lead_id = lead.id

#     # parse ISO (keep it strict; Vapi should send ISO)
#     try:
#         start = datetime.fromisoformat(payload.start_time_iso.replace("Z", "+00:00"))
#     except Exception:
#         raise HTTPException(status_code=422, detail="Invalid start_time_iso")

#     end = start + timedelta(minutes=payload.duration_minutes)

#     booking = models.Booking(
#         call_id=call.id,
#         lead_id=lead.id,
#         calendar_provider="google_calendar",  # change if using cal.com link-only
#         calendar_event_id=None,              # fill once you integrate API
#         start_time=start,
#         end_time=end,
#         timezone=payload.timezone,
#         meeting_link=None,
#         status="booked",
#     )
#     db.add(booking)

#     # Mark outcome on the call
#     call.outcome_tag = "#audit-booked"  # pyright: ignore[reportAttributeAccessIssue]

#     db.flush()

#     resp = {"booking_id": str(booking.id), "status": "booked", "calendar_event_id": None, "meeting_link": None}
#     log_tool_call(db, call.id, "bookAudit", payload.model_dump(), resp)

#     db.commit()
#     return BookAuditResponse(**resp)


@router.post("/outcome/log", response_model=OutcomeLogResponse)
def log_outcome(
    payload: OutcomeLogRequest,
    agent: Agent = Depends(get_agent_from_key),
    db: Session = Depends(get_db),
) -> OutcomeLogResponse:
    org_id = agent.organization_id
    call = get_or_create_call(db, payload.call_id, org_id, agent.id)

    call.outcome_tag = payload.outcome_tag  # pyright: ignore[reportAttributeAccessIssue]
    call.outcome_note = payload.note

    resp = {"ok": True}
    log_tool_call(db, org_id, call.id, "logOutcome", payload.model_dump(mode="json"), resp)

    db.commit()
    return OutcomeLogResponse(**resp)


@router.post("/handoff/request", response_model=HandoffResponse)
def handoff_request(
    payload: HandoffRequest,
    agent: Agent = Depends(get_agent_from_key),
    db: Session = Depends(get_db),
) -> HandoffResponse:
    org_id = agent.organization_id
    call = get_or_create_call(db, payload.call_id, org_id, agent.id)

    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == uuid.UUID(payload.lead_id), models.Lead.organization_id == org_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not call.lead_id:
        call.lead_id = lead.id

    handoff = models.Handoff(
        organization_id=org_id,
        call_id=call.id,
        lead_id=lead.id,
        reason=payload.reason,
        target_phone=payload.target_phone,
        status="queued",
    )
    db.add(handoff)
    db.flush()

    resp = {"handoff_id": str(handoff.id), "status": "queued", "instruction": "I’m connecting you now. One moment please."}
    log_tool_call(db, org_id, call.id, "handoffRequest", payload.model_dump(mode="json"), resp)

    db.commit()
    return HandoffResponse(**resp)  # pyright: ignore[reportArgumentType]
