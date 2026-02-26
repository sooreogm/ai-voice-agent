import enum


class LeakTag(str, enum.Enum):
    leak_speed = "#leak-speed"
    leak_fragmentation = "#leak-fragmentation"
    leak_followup = "#leak-followup"
    leak_booking = "#leak-booking"
    leak_traffic = "#leak-traffic"


class OutcomeTag(str, enum.Enum):
    audit_booked = "#audit-booked"
    requested_info = "#requested-info"
    callback_scheduled = "#callback-scheduled"
    parked = "#parked"
    not_a_fit = "#not-a-fit"
    no_answer = "#no-answer"


class ResponseSpeed(str, enum.Enum):
    under_10_min = "under_10_min"
    within_hour = "within_hour"
    same_day = "same_day"
    later = "later"
    unknown = "unknown"


class PrimaryIntent(str, enum.Enum):
    more_enquiries = "more_enquiries"
    enquiries_not_converting = "enquiries_not_converting"
    stop_going_cold = "stop_going_cold"
    unknown = "unknown"


class BookingStatus(str, enum.Enum):
    booked = "booked"
    cancelled = "cancelled"
    rescheduled = "rescheduled"


class HandoffStatus(str, enum.Enum):
    queued = "queued"
    completed = "completed"
    cancelled = "cancelled"


class UseCase(str, enum.Enum):
    lead_qualification = "lead_qualification"
    appointment_booking = "appointment_booking"
    support = "support"
    custom = "custom"


class OrgRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
