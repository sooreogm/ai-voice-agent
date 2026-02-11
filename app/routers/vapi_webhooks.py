from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.deps import require_vapi_key
from app.db import get_db
from app import models

router = APIRouter(prefix="/webhooks/vapi", tags=["vapi-webhooks"], dependencies=[Depends(require_vapi_key)])


class VapiEvent(BaseModel):
    event: str
    call_id: str
    payload: Dict[str, Any]


@router.post("/events")
def vapi_events(evt: VapiEvent, db: Session = Depends(get_db)) -> Dict[str, bool]:
    call = db.query(models.Call).filter(models.Call.vapi_call_id == evt.call_id).first()
    if not call:
        call = models.Call(vapi_call_id=evt.call_id)
        db.add(call)
        db.flush()

    # Common fields (vary by Vapi configuration)
    p = evt.payload or {}

    if evt.event in {"call.started", "call.start"}:
        # If timestamp exists in payload, parse; else leave null
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

        # optional recording URL
        rec = p.get("recordingUrl") or p.get("recording_url")
        if rec:
            call.recording_url = rec

    # transcript payloads often arrive as separate events; store as append
    if evt.event in {"transcript", "call.transcript", "call.transcript.partial", "call.transcript.final"}:
        text = p.get("text") or p.get("transcript")
        if text:
            call.transcript = (call.transcript or "") + (("\n" if call.transcript else "") + text)

    db.add(
        models.ToolCall(
            call_id=call.id,
            tool_name=f"webhook:{evt.event}",
            request_json={"event": evt.event, "call_id": evt.call_id, "payload": evt.payload},
            response_json={"ok": True},
            success=True,
        )
    )

    db.commit()
    return {"ok": True}
