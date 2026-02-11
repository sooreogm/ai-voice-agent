
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from loguru import logger
from app.deps import require_vapi_key
from app.schemas.bookings import CalComAvailabilityResponse, CalComBookingResponse, CalComBookingsListResponse, CreateBookingRequest
from app.schemas.responses import SuccessResponse
from app.services.bookings import create_booking, get_availability, list_bookings
from app.utils.responses import responses_example


router = APIRouter(prefix="/bookings", tags=["Bookings"], dependencies=[Depends(require_vapi_key)])

@router.get(
    "",
    responses=responses_example(),
    response_model=SuccessResponse[CalComBookingsListResponse],
    status_code=status.HTTP_200_OK,
)
async def list_cal_com_bookings(
    time_min: Optional[str] = Query(None, description="Minimum time (ISO 8601)"),
    time_max: Optional[str] = Query(None, description="Maximum time (ISO 8601)"),
    event_type_id: Optional[int] = Query(None, description="Event type ID to filter"),
):
    try:
        # Parse datetime strings if provided
        time_min_dt = None
        time_max_dt = None
        
        if time_min:
            try:
                time_min_dt = datetime.fromisoformat(time_min.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid time_min format. Use ISO 8601 format (e.g., 2026-01-27T10:00:00Z)"
                )
        
        if time_max:
            try:
                time_max_dt = datetime.fromisoformat(time_max.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid time_max format. Use ISO 8601 format (e.g., 2026-01-27T18:00:00Z)"
                )
        
        result = list_bookings(
            # user_id=current_admin.id,
            time_min=time_min_dt,
            time_max=time_max_dt,
            event_type_id=event_type_id,
        )
        
        return SuccessResponse(
            isSuccess=True,
            message=f"Retrieved {len(result.bookings)} bookings",
            data=result,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing Cal.com bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list bookings"
        ) from e
        
@router.post(
    "",
    responses=responses_example(),
    response_model=SuccessResponse[CalComBookingResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_cal_com_booking(
    booking_data: CreateBookingRequest,
):
    try:
        # Apply defaults if not provided
        now = datetime.now(timezone.utc)
        
        # Set default start time to now if not provided
        if booking_data.start is None:
            booking_data.start = now
        
        # Set default end time to 15 minutes from start if not provided
        if booking_data.end is None:
            # Get start time as datetime object
            start_time = booking_data.start if booking_data.start else now
            
            # Ensure timezone-aware
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            
            booking_data.end = start_time + timedelta(minutes=15)
        
        booking = create_booking(
            user_id=booking_data.email,
            booking_data=booking_data,
        )
        
        return SuccessResponse(
            isSuccess=True,
            message="Booking created successfully",
            data=booking,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Cal.com booking: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking"
        ) from e

@router.get(
    "/availability",
    responses=responses_example(),
    response_model=SuccessResponse[CalComAvailabilityResponse],
    status_code=status.HTTP_200_OK,
)
async def get_available_slots(
    start: Optional[str] = Query(None, description="Start time (ISO 8601 UTC, e.g., 2026-01-27T00:00:00Z). Defaults to today at 00:00:00 UTC."),
    end: Optional[str] = Query(None, description="End time (ISO 8601 UTC, e.g., 2026-01-28T23:59:59Z). Defaults to 4 weeks from today at 23:59:59 UTC."),
    event_type_id: Optional[int] = Query(None, description="Event type ID (uses default from settings if not provided)"),
    time_zone: Optional[str] = Query(None, description="Time zone for returned slots (e.g., Europe/London, defaults to UTC)"),
    duration: Optional[int] = Query(None, description="Duration in minutes (for multi-duration event types)"),
    format: Optional[str] = Query(None, description="Format: 'range' for start/end times, 'time' for start only"),
):
    try:
        # Set defaults if not provided
        now = datetime.now(timezone.utc)
        
        if start is None:
            # Default to today at 00:00:00 UTC
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            try:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start format. Use ISO 8601 format (e.g., 2026-01-27T00:00:00Z)"
                )
        
        if end is None:
            # Default to 4 weeks from today at 23:59:59 UTC
            end_dt = (now + timedelta(weeks=4)).replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            try:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end format. Use ISO 8601 format (e.g., 2026-01-28T23:59:59Z)"
                )
        
        # Validate date range
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time"
            )
        
        availability = get_availability(
            start=start_dt,
            end=end_dt,
            event_type_id=event_type_id,
            time_zone=time_zone,
            duration=duration,
            format=format,
        )
        
        total_slots = sum(len(slots) for slots in availability.slots.values())
        
        return SuccessResponse(
            isSuccess=True,
            message=f"Retrieved {total_slots} available slots across {len(availability.slots)} days",
            data=availability,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting availability: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve availability"
        ) from e
