import json
from typing import cast
from vapi import CreateApiRequestToolDto, JsonSchema
from app.config import get_settings

BASE_URL = get_settings().SERVER_BASE_URL.rstrip("/")
VAPI_BASE_URL = "https://api.vapi.ai"
TOOL_API_KEY = get_settings().VAPI_TOOL_API_KEY

TOOLS = [
    # 1) Lead upsert
    {
        "type": "apiRequest",
        "function": {"name": "api_request_tool"},
        "name": "upsertLead",
        "method": "POST",
        "url": f"{BASE_URL}/api/tools/leads/upsert",
        "headers": {
            "type": "object",
            "properties": {
                "x-api-key": {"type": "string", "value": TOOL_API_KEY},
            },
        },
        # OpenAPI: UpsertLeadRequest requires phone; call_id is nullable
        # We still require call_id + phone in tool schema to force consistent logging.
        "body": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string", "description": "Vapi call id"},
                "phone": {"type": "string"},
                "name": {"type": "string"},
                "business_name": {"type": "string"},
                "role": {"type": "string"},
                "email": {"type": "string"},
                "industry": {"type": "string"},
                "location": {"type": "string"},
                "source": {"type": "string", "enum": ["inbound_call"]},
                "notes": {"type": "string"},
            },
            "required": ["call_id", "phone"],
        },
    },

    # 2) Fit check (OpenAPI FitCheckSaveRequest)
    {
        "type": "apiRequest",
        "function": {"name": "api_request_tool"},
        "name": "saveFitCheck",
        "method": "POST",
        "url": f"{BASE_URL}/api/tools/fit-check/save",
        "headers": {
            "type": "object",
            "properties": {
                "x-api-key": {"type": "string", "value": TOOL_API_KEY},
            },
        },
        "body": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string"},
                "lead_id": {"type": "string", "format": "uuid"},
                "business_offer": {"type": "string"},
                "lead_sources": {"type": "array", "items": {"type": "string"}},
                "weekly_enquiries": {"type": "string"},
                "response_speed": {
                    "type": "string",
                    "enum": ["under_10_min", "within_hour", "same_day", "later", "unknown"],
                },
                "booking_method": {"type": "string"},
                "has_followup_system": {"type": "boolean"},
                "capacity_next_weeks": {"type": "boolean"},
                "primary_intent": {
                    "type": "string",
                    "enum": ["more_enquiries", "enquiries_not_converting", "stop_going_cold", "unknown"],
                },
            },
            "required": ["call_id", "lead_id"],
        },
    },

    # 3) Diagnosis + tag (OpenAPI QualifyRequest)
    {
        "type": "apiRequest",
        "function": {"name": "api_request_tool"},
        "name": "qualifyAndTag",
        "method": "POST",
        "url": f"{BASE_URL}/api/tools/qualification/score",
        "headers": {
            "type": "object",
            "properties": {
                "x-api-key": {"type": "string", "value": TOOL_API_KEY},
            },
        },
        "body": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string"},
                "lead_id": {"type": "string", "format": "uuid"},
                "diagnosis_tag": {
                    "type": "string",
                    "enum": [
                        "#leak-speed",
                        "#leak-fragmentation",
                        "#leak-followup",
                        "#leak-booking",
                        "#leak-traffic",
                    ],
                },
                "one_sentence_summary": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["call_id", "lead_id"],
        },
    },

    # 4) Outcome log (OpenAPI OutcomeLogRequest)
    {
        "type": "apiRequest",
        "function": {"name": "api_request_tool"},
        "name": "logOutcome",
        "method": "POST",
        "url": f"{BASE_URL}/api/tools/outcome/log",
        "headers": {
            "type": "object",
            "properties": {
                "x-api-key": {"type": "string", "value": TOOL_API_KEY},
            },
        },
        "body": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string"},
                "lead_id": {"type": "string"},
                "outcome_tag": {
                    "type": "string",
                    "enum": [
                        "#audit-booked",
                        "#requested-info",
                        "#callback-scheduled",
                        "#parked",
                        "#not-a-fit",
                        "#no-answer",
                    ],
                },
                "note": {"type": "string"},
            },
            # OpenAPI requires call_id + outcome_tag; your prompt wants note “required in practice”
            "required": ["call_id", "outcome_tag", "note"],
        },
    },

    # 5) Handoff (OpenAPI HandoffRequest)
    {
        "type": "apiRequest",
        "function": {"name": "api_request_tool"},
        "name": "handoffRequest",
        "method": "POST",
        "url": f"{BASE_URL}/api/tools/handoff/request",
        "headers": {
            "type": "object",
            "properties": {
                "x-api-key": {"type": "string", "value": TOOL_API_KEY},
            },
        },
        "body": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string"},
                "lead_id": {"type": "string"},
                "reason": {"type": "string"},
                "target_phone": {"type": "string"},
            },
            "required": ["call_id", "lead_id", "reason"],
        },
    },

    # 6) Availability (OpenAPI GET /api/bookings/availability)
    {
        "type": "apiRequest",
        "function": {"name": "api_request_tool"},
        "name": "getAvailability",
        "method": "GET",
        "url": f"{BASE_URL}/api/bookings/availability?start={{start}}&end={{end}}",
        "headers": {
            "type": "object",
            "properties": {
                "x-api-key": {"type": "string", "value": TOOL_API_KEY},
            },
        },
        "body": {
            "type": "object",
            "properties": {
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
            "required": ["start", "end"],
        },
    },

    # 7) Book audit (OpenAPI POST /api/bookings)
    {
        "type": "apiRequest",
        "function": {"name": "api_request_tool"},
        "name": "bookAudit",
        "method": "POST",
        "url": f"{BASE_URL}/api/bookings",
        "headers": {
            "type": "object",
            "properties": {
                "x-api-key": {"type": "string", "value": TOOL_API_KEY},
            },
        },
        "body": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "name": {"type": "string"},
                "phoneNumber": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
                # attendees optional; only use if you truly need them
                "attendees": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                            "phoneNumber": {"type": "string"},
                        },
                        "required": ["name", "email", "phoneNumber"],
                    },
                },
            },
            # OpenAPI requires email + name; we require start+end too for deterministic scheduling
            "required": ["name", "email", "start", "end"],
        },
    },
]
