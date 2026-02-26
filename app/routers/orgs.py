import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_organization, get_current_user
from app.models import Agent, Booking, Call, Lead, Organization, OrganizationMember, ToolCall, User
from app.models.enums import OrgRole
from app.schemas.agents import AgentCreate, AgentOut, AgentUpdate
from app.schemas.dashboard import BookingListItem, CallDetail, CallListItem, LeadListItem, ToolCallItem
from app.schemas.orgs import OrganizationCreate, OrganizationOut, OrganizationUpdate

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
def list_orgs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .all()
    )
    org_ids = [m.organization_id for m in memberships]
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    return [OrganizationOut.model_validate(o) for o in orgs]


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_org(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(Organization).filter(Organization.slug == data.slug).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists",
        )
    org = Organization(name=data.name, slug=data.slug, business_context=data.business_context)
    db.add(org)
    db.flush()
    member = OrganizationMember(
        user_id=current_user.id,
        organization_id=org.id,
        role=OrgRole.owner,
    )
    db.add(member)
    db.commit()
    db.refresh(org)
    return OrganizationOut.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationOut)
def get_org(
    org: Organization = Depends(get_current_organization),
):
    return OrganizationOut.model_validate(org)


@router.patch("/{org_id}", response_model=OrganizationOut)
def update_org(
    data: OrganizationUpdate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    if data.name is not None:
        org.name = data.name
    if data.business_context is not None:
        org.business_context = data.business_context
    db.commit()
    db.refresh(org)
    return OrganizationOut.model_validate(org)


# --- Agents (nested under org) ---

@router.get("/{org_id}/agents", response_model=list[AgentOut])
def list_agents(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    agents = db.query(Agent).filter(Agent.organization_id == org.id).all()
    return [_agent_out(a) for a in agents]


@router.post("/{org_id}/agents", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
def create_agent(
    data: AgentCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    tool_api_key = "sk_" + secrets.token_urlsafe(32)
    agent = Agent(
        organization_id=org.id,
        name=data.name,
        use_case=data.use_case,
        prompt=data.prompt,
        first_message=data.first_message,
        model_provider=data.model_provider or "openai",
        model=data.model or "gpt-4o",
        model_temperature=data.model_temperature,
        voice_provider=data.voice_provider or "11labs",
        voice_id=data.voice_id,
        cal_com_api_key=data.cal_com_api_key,
        tool_api_key=tool_api_key,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return _agent_out(agent)


@router.get("/{org_id}/agents/{agent_id}", response_model=AgentOut)
def get_agent(
    agent_id: UUID,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == org.id,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_out(agent)


@router.patch("/{org_id}/agents/{agent_id}", response_model=AgentOut)
def update_agent(
    agent_id: UUID,
    data: AgentUpdate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == org.id,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if data.name is not None:
        agent.name = data.name
    if data.use_case is not None:
        agent.use_case = data.use_case
    if data.prompt is not None:
        agent.prompt = data.prompt
    if data.first_message is not None:
        agent.first_message = data.first_message
    if data.model_provider is not None:
        agent.model_provider = data.model_provider
    if data.model is not None:
        agent.model = data.model
    if data.model_temperature is not None:
        agent.model_temperature = data.model_temperature
    if data.voice_provider is not None:
        agent.voice_provider = data.voice_provider
    if data.voice_id is not None:
        agent.voice_id = data.voice_id
    if data.cal_com_api_key is not None:
        agent.cal_com_api_key = data.cal_com_api_key
    db.commit()
    db.refresh(agent)
    return _agent_out(agent)


def _agent_out(agent: Agent) -> AgentOut:
    return AgentOut(
        id=str(agent.id),
        organization_id=str(agent.organization_id),
        name=agent.name,
        use_case=agent.use_case.value,
        prompt=agent.prompt,
        first_message=agent.first_message,
        model_provider=agent.model_provider,
        model=agent.model,
        voice_provider=agent.voice_provider,
        voice_id=agent.voice_id,
        vapi_assistant_id=agent.vapi_assistant_id,
        cal_com_event_type_id=agent.cal_com_event_type_id,
        created_at=agent.created_at,
    )


# --- Dashboard: calls, leads, bookings (scoped by org) ---

@router.get("/{org_id}/calls", response_model=list[CallListItem])
def list_calls(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    calls = (
        db.query(Call)
        .filter(Call.organization_id == org.id)
        .order_by(Call.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        CallListItem(
            id=str(c.id),
            vapi_call_id=c.vapi_call_id,
            started_at=c.started_at,
            ended_at=c.ended_at,
            duration_sec=c.duration_sec,
            outcome_tag=c.outcome_tag.value if c.outcome_tag else None,
            recording_url=c.recording_url,
            created_at=c.created_at,
        )
        for c in calls
    ]


@router.get("/{org_id}/calls/{call_id}", response_model=CallDetail)
def get_call_detail(
    call_id: UUID,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.organization_id == org.id,
    ).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    lead = None
    if call.lead_id:
        lead_obj = db.query(Lead).filter(Lead.id == call.lead_id).first()
        if lead_obj:
            lead = LeadListItem(
                id=str(lead_obj.id),
                name=lead_obj.name,
                business_name=lead_obj.business_name,
                phone=lead_obj.phone,
                email=lead_obj.email,
                source=lead_obj.source,
                created_at=lead_obj.created_at,
            )
    tool_calls = (
        db.query(ToolCall)
        .filter(ToolCall.call_id == call.id)
        .order_by(ToolCall.created_at)
        .all()
    )
    return CallDetail(
        id=str(call.id),
        vapi_call_id=call.vapi_call_id,
        organization_id=str(call.organization_id),
        agent_id=str(call.agent_id) if call.agent_id else None,
        started_at=call.started_at,
        ended_at=call.ended_at,
        duration_sec=call.duration_sec,
        transcript=call.transcript,
        recording_url=call.recording_url,
        outcome_tag=call.outcome_tag.value if call.outcome_tag else None,
        outcome_note=call.outcome_note,
        created_at=call.created_at,
        lead=lead,
        tool_calls=[
            ToolCallItem(
                id=str(tc.id),
                tool_name=tc.tool_name,
                request_json=tc.request_json,
                response_json=tc.response_json,
                success=tc.success,
                created_at=tc.created_at,
            )
            for tc in tool_calls
        ],
    )


@router.get("/{org_id}/leads", response_model=list[LeadListItem])
def list_leads(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    leads = (
        db.query(Lead)
        .filter(Lead.organization_id == org.id)
        .order_by(Lead.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        LeadListItem(
            id=str(l.id),
            name=l.name,
            business_name=l.business_name,
            phone=l.phone,
            email=l.email,
            source=l.source,
            created_at=l.created_at,
        )
        for l in leads
    ]


@router.get("/{org_id}/bookings", response_model=list[BookingListItem])
def list_bookings(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    bookings = (
        db.query(Booking)
        .filter(Booking.organization_id == org.id)
        .order_by(Booking.start_time.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        BookingListItem(
            id=str(b.id),
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status.value,
            meeting_link=b.meeting_link,
            created_at=b.created_at,
        )
        for b in bookings
    ]
