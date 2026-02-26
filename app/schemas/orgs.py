from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-z0-9\-]+$")
    business_context: dict | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    business_context: dict | None = None


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    business_context: dict | None = None

    class Config:
        from_attributes = True
