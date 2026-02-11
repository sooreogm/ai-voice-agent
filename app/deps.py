import os
from fastapi import Header, HTTPException

SECRET = os.getenv("VAPI_TOOL_API_KEY", "")

from fastapi import Header, HTTPException, Depends
from app.config import get_settings, Settings

def require_vapi_key(
    settings: Settings = Depends(get_settings),
    x_api_key: str | None = Header(default=None, alias="X-API-KEY"),
) -> None:
    if x_api_key != settings.VAPI_TOOL_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

