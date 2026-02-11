from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    VAPI_API_TOKEN: str = Field(..., min_length=20)
    VAPI_TOOL_API_KEY: str = Field(..., min_length=20)
    DATABASE_URL: str = Field(..., min_length=20)
    LOG_LEVEL: str = "INFO"
    CAL_COM_BASE_URL: str = "https://api.cal.com/v2"
    CAL_COM_API_KEY: str = Field(..., min_length=20)
    CAL_COM_EVENT_TYPE_ID: int 
    ASSISTANT_ID: str
    SERVER_BASE_URL: str 
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "https://staging.klarnow.ai", "https://klarnow.ai"],
        alias="CORS_ORIGINS"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]

