from uuid import UUID

from fastapi import Depends, Header, Path
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings, Settings
from app.db import get_db
from app.models import Agent, Organization, OrganizationMember, User
from app.utils.auth import decode_access_token

security = HTTPBearer(auto_error=False)


def require_vapi_key(
    settings: Settings = Depends(get_settings),
    x_api_key: str | None = Header(default=None, alias="X-API-KEY"),
) -> None:
    """Legacy: single platform key. Prefer require_agent_key for SaaS."""
    key = settings.VAPI_TOOL_API_KEY
    if not key or x_api_key != key:
        raise HTTPException(status_code=401, detail="Unauthorized")


def get_current_user(
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    sub = decode_access_token(creds.credentials)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == UUID(sub), User.is_active).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_agent_from_key(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-KEY"),
) -> Agent:
    """Resolve org/agent from per-agent tool API key (VAPI tool requests)."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-KEY")
    agent = db.query(Agent).filter(Agent.tool_api_key == x_api_key).first()
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return agent


def get_current_organization(
    org_id: UUID = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    """Require user to be a member of the given org (from path)."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return org
