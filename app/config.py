from functools import lru_cache
from typing import Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(v: Union[list[str], str]) -> list[str]:
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str = Field(..., min_length=20)
    SERVER_BASE_URL: str = Field(...)
    VAPI_API_TOKEN: str = Field(..., min_length=20)
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    CAL_COM_BASE_URL: str = "https://api.cal.com/v2"
    # Optional: for backward compat or platform default (e.g. trials)
    VAPI_TOOL_API_KEY: str | None = Field(default=None, min_length=20)
    CAL_COM_API_KEY: str | None = Field(default=None, min_length=20)
    CAL_COM_EVENT_TYPE_ID: int | None = None
    ASSISTANT_ID: str | None = None
    # JWT auth (set JWT_SECRET in production)
    JWT_SECRET: str = Field(default="change-me-in-production-min-32-chars", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS (env can be comma-separated string, e.g. CORS_ORIGINS="http://a.com,http://b.com")
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "https://staging.klarnow.ai",
            "https://klarnow.ai",
        ],
        alias="CORS_ORIGINS",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[list[str], str]) -> list[str]:
        return _parse_cors_origins(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]

