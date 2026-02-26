from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app import models

router = APIRouter(prefix="/webhooks/vapi", tags=["vapi-webhooks"])


class VapiEvent(BaseModel):
    event: str
    call_id: str
    payload: Dict[str, Any]


def _get_assistant_id(payload: Dict[str, Any]) -> str | None:
    p = payload or {}
    return p.get("assistantId") or (p.get("message") or {}).get("assistantId")


@router.post("/events")
def vapi_events(evt: VapiEvent, db: Session = Depends(get_db)) -> Dict[str, bool]:
    assistant_id = _get_assistant_id(evt.payload)
    agent = None
    if assistant_id:
        agent = db.query(models.Agent).filter(models.Agent.vapi_assistant_id == assistant_id).first()
    if not agent:
        logger.warning("VAPI webhook: no assistantId or agent not found, skipping call update")
        return {"ok": True}

    org_id = agent.organization_id
    agent_id = agent.id

    call = (
        db.query(models.Call)
        .filter(
            models.Call.organization_id == org_id,
            models.Call.vapi_call_id == evt.call_id,
        )
        .first()
    )
    if not call:
        call = models.Call(
            vapi_call_id=evt.call_id,
            organization_id=org_id,
            agent_id=agent_id,
        )
        db.add(call)
        db.flush()

    p = evt.payload or {}

    if evt.event in {"call.started", "call.start"}:
        ts = p.get("startedAt") or p.get("startTime")
        if ts:
            try:
                call.started_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass

    if evt.event in {"call.ended", "call.end"}:
        ts = p.get("endedAt") or p.get("endTime")
        if ts:
            try:
                call.ended_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass
        if p.get("durationSec") is not None:
            call.duration_sec = int(p["durationSec"])
        rec = p.get("recordingUrl") or p.get("recording_url")
        if rec:
            call.recording_url = rec

    if evt.event in {"transcript", "call.transcript", "call.transcript.partial", "call.transcript.final"}:
        text = p.get("text") or p.get("transcript")
        if text:
            call.transcript = (call.transcript or "") + (("\n" if call.transcript else "") + text)

    db.add(
        models.ToolCall(
            organization_id=org_id,
            call_id=call.id,
            tool_name=f"webhook:{evt.event}",
            request_json={"event": evt.event, "call_id": evt.call_id, "payload": evt.payload},
            response_json={"ok": True},
            success=True,
        )
    )

    db.commit()
    return {"ok": True}
