from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator


class AttendeeRequest(BaseModel):
    """Schema for an attendee."""
    name: str = Field(..., description="Attendee name")
    email: str = Field(..., description="Attendee email")
    phoneNumber: str = Field(..., description="Attendee phone number")


class CreateBookingRequest(BaseModel):
    """Request schema for creating a booking."""
    email: str = Field(..., description="Primary attendee email")
    name: str = Field(..., description="Primary attendee name")
    phoneNumber: Optional[Union[str, dict]] = Field(None, description="Primary attendee phone number (string or object with 'number' field)")
    
    @field_validator('phoneNumber', mode='before')
    @classmethod
    def extract_phone_number(cls, v):
        """Extract phone number from object if needed."""
        if v is None:
            return None
        if isinstance(v, dict):
            # Extract the 'number' field from the object
            return v.get('number', None)
        if isinstance(v, str):
            # Skip if it's "unknown" or empty
            if v.lower() in ('unknown', 'none', ''):
                return None
        return v
    start: Optional[datetime] = Field(None, description="Start time. Defaults to current time.")
    end: Optional[datetime] = Field(None, description="End time. Defaults to 15 minutes from start.")
    attendees: Optional[list[AttendeeRequest]] = Field(None, description="Additional attendees with name, email, and phone number")


class UpdateBookingRequest(BaseModel):
    """Request schema for updating/rescheduling a booking."""
    start: Optional[datetime] = Field(None, description="New start time")
    end: Optional[datetime] = Field(None, description="New end time")
    notes: Optional[str] = Field(None, description="Updated booking notes")
    location: Optional[str] = Field(None, description="Updated meeting location")


class CalComBookingResponse(BaseModel):
    """Response schema for Cal.com bookings."""
    id: Optional[int] = Field(None, description="Booking ID")
    title: Optional[str] = Field(None, description="Booking title")
    description: Optional[str] = Field(None, description="Booking description")
    startTime: Optional[str] = Field(None, description="Start time (ISO 8601)")
    endTime: Optional[str] = Field(None, description="End time (ISO 8601)")
    attendees: Optional[list[dict]] = Field(None, description="List of attendees")
    location: Optional[str] = Field(None, description="Meeting location")
    status: Optional[str] = Field(None, description="Booking status")
    uid: Optional[str] = Field(None, description="Unique booking identifier")
    bookingUrl: Optional[str] = Field(None, description="URL to view booking")
    meetingUrl: Optional[str] = Field(None, description="Meeting URL (video call link)")

    class Config:
        from_attributes = True


class CalComBookingsListResponse(BaseModel):
    """Response schema for list of Cal.com bookings."""
    bookings: list[CalComBookingResponse] = Field(..., description="List of bookings")


class TimeSlot(BaseModel):
    """Schema for a time slot."""
    start: str = Field(..., description="Start time (ISO 8601)")
    end: Optional[str] = Field(None, description="End time (ISO 8601), only present when format=range")


class CalComAvailabilityResponse(BaseModel):
    """Response schema for Cal.com availability slots."""
    slots: dict[str, list[TimeSlot]] = Field(..., description="Map of available slots indexed by date (YYYY-MM-DD)")
