import httpx
import re
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from loguru import logger

from app.config import get_settings
from app.schemas.bookings import (
    CalComAvailabilityResponse,
    CalComBookingResponse,
    CalComBookingsListResponse,
    CreateBookingRequest,
    TimeSlot,
)

BASE_URL = get_settings().CAL_COM_BASE_URL


def get_api_key() -> str:
    if not get_settings().CAL_COM_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cal.com API key not configured. Please set CAL_COM_API_KEY."
        )
    return get_settings().CAL_COM_API_KEY

def _to_utc_z(dt):  
    if dt.tzinfo is None:               
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.isoformat().replace("+00:00", "Z")


def _normalize_phone_number(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None

    raw = phone.strip()
    if raw.lower() in {"unknown", "none", ""}:
        return None

    cleaned = re.sub(r"[^\d+]", "", raw)  # keep digits and '+'
    if not cleaned:
        return None

    # Already E.164-ish
    if cleaned.startswith("+"):
        return cleaned

    # UK heuristics
    if cleaned.startswith("0"):
        return "+44" + cleaned[1:]
    if cleaned.startswith("44"):
        return "+" + cleaned
    if re.fullmatch(r"\d{10,11}", cleaned):
        return "+44" + cleaned

    # US/Canada heuristic
    if cleaned.startswith("1"):
        return "+" + cleaned

    # Fallback: force leading '+'
    logger.warning(f"Could not normalize phone number format: {phone}, returning as: {cleaned}")
    return "+" + cleaned
    
def list_bookings(
    # user_id: UUID,
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    event_type_id: Optional[int] = None,
) -> CalComBookingsListResponse:
    api_key = get_api_key()
    
    params = {}
    
    if time_min:
        if isinstance(time_min, datetime):
            params["startTime"] = time_min.isoformat() + "Z" if time_min.tzinfo is None else time_min.isoformat()
        else:
            params["startTime"] = time_min
    
    if time_max:
        if isinstance(time_max, datetime):
            params["endTime"] = time_max.isoformat() + "Z" if time_max.tzinfo is None else time_max.isoformat()
        else:
            params["endTime"] = time_max
    
    if event_type_id:
        params["eventTypeId"] = event_type_id  # pyright: ignore[reportArgumentType]
    
    try:
        response = httpx.get(
            f"{BASE_URL}/bookings",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data: dict = response.json()

        print(data) 
        
        bookings = []
        for item in dict(data.get("data", {})).get("bookings", []):
            booking = CalComBookingResponse(
                id=item.get("id"),
                title=item.get("title"),
                description=item.get("description"),
                startTime=item.get("startTime"),
                endTime=item.get("endTime"),
                attendees=item.get("attendees", []),
                location=item.get("location"),
                status=item.get("status"),
                uid=item.get("uid"),
                bookingUrl=item.get("bookingUrl"),
                meetingUrl=item.get("meetingUrl"),
            )
            bookings.append(booking)
        
        logger.info(f"Retrieved {len(bookings)} bookings for user")
        return CalComBookingsListResponse(
            bookings=bookings,
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Cal.com API error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cal.com API authentication failed. Please check your API key."
            ) from e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cal.com API error: {e.response.status_code}"
        ) from e
    except Exception as e:
        logger.error(f"Error listing Cal.com bookings for user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings"
        ) from e

def create_booking(
    user_id: str,
    booking_data: CreateBookingRequest,
) -> CalComBookingResponse:
    api_key = get_api_key()

    if booking_data.start is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time is required",
        )

    payload = {
        "eventTypeId": int(get_settings().CAL_COM_EVENT_TYPE_ID),
        "start": _to_utc_z(booking_data.start),
        "attendee": {
            "name": booking_data.name,
            "email": booking_data.email,
            "timeZone": "Europe/London",
            "language": "en",
        },
        "metadata": {},
    }

    # If SMS reminders are enabled on the event type, phoneNumber becomes required
    phone_number = getattr(booking_data, "phoneNumber", None)
    if phone_number:
        # Normalize phone number to E.164 format for Cal.com
        normalized_phone = _normalize_phone_number(phone_number)
        # Only add phone number if it's valid (not "unknown" or empty)
        if normalized_phone and normalized_phone.lower() not in ('unknown', 'none', ''):
            payload["attendee"]["phoneNumber"] = normalized_phone

    # Additional attendees => use guests (list of emails) in v2
    guests = []
    if booking_data.attendees:
        for a in booking_data.attendees:
            if a.email:
                guests.append(a.email)
    if guests:
        payload["guests"] = guests

    try:
        resp = httpx.post(
            f"{BASE_URL}/bookings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "cal-api-version": "2024-08-13",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )
        resp.raise_for_status()

        data = resp.json()
        item = data.get("data", data)

        booking = CalComBookingResponse(
            id=item.get("id"),
            title=item.get("title"),
            description=item.get("description"),
            startTime=item.get("start"),
            endTime=item.get("end"),
            attendees=item.get("attendees", []),
            location=item.get("location"),
            status=item.get("status"),
            uid=item.get("uid"),
            bookingUrl=item.get("bookingUrl"),
            meetingUrl=item.get("meetingUrl"),
        )

        logger.info(f"Created Cal.com booking {booking.id} for user {user_id}")
        return booking

    except httpx.HTTPStatusError as e:
        logger.error(f"Cal.com API error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cal.com API authentication failed. Please check your API key.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cal.com API error: {e.response.status_code}",
        ) from e

def get_availability(
    # user_id: UUID,
    start: datetime,
    end: datetime,
    event_type_id: Optional[int] = None,
    time_zone: Optional[str] = None,
    duration: Optional[int] = None,
    format: Optional[str] = None,
) -> CalComAvailabilityResponse:
    api_key = get_api_key()
    
    # Use event type from settings if not provided
    if event_type_id is None:
        event_type_id = int(get_settings().CAL_COM_EVENT_TYPE_ID)
    
    # Build query parameters
    params = {
        "eventTypeId": event_type_id,
        "start": _to_utc_z(start),
        "end": _to_utc_z(end),
    }
    
    if time_zone:
        params["timeZone"] = time_zone
    
    if duration:
        params["duration"] = duration
    
    if format:
        params["format"] = format
    
    try:
        response = httpx.get(
            f"{BASE_URL}/slots",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "cal-api-version": "2024-09-04",
            },
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        data: dict = response.json()
        
        # Parse the response data
        slots_data = data.get("data", {})
        
        # Convert to our schema format
        slots: dict[str, list[TimeSlot]] = {}
        for date_str, slot_list in slots_data.items():
            slots[date_str] = []
            for slot_item in slot_list:
                if isinstance(slot_item, dict):
                    slot = TimeSlot(
                        start=slot_item.get("start", ""),
                        end=slot_item.get("end"),
                    )
                    slots[date_str].append(slot)
                elif isinstance(slot_item, str):
                    # If format is 'time', slots might be just strings
                    slot = TimeSlot(start=slot_item, end=None)
                    slots[date_str].append(slot)
        
        logger.info(f"Retrieved availability for user from {start} to {end}")
        return CalComAvailabilityResponse(slots=slots)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Cal.com API error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cal.com API authentication failed. Please check your API key."
            ) from e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cal.com API error: {e.response.status_code}"
        ) from e
    except Exception as e:
        logger.error(f"Error getting Cal.com availability for user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve availability"
        ) from e
