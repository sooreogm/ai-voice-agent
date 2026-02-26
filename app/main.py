from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.routers import auth, bookings, orgs, tools, vapi_webhooks
from app.utils.api_utils import tags_metadata
from app.utils.logging import setup_logging
from app.utils.responses import error_response
from fastapi.openapi.utils import get_openapi

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(get_settings().LOG_LEVEL)
    yield

app = FastAPI(
    title="Klarnow Voice Agent API",
    description="""Klarnow Voice Agent API""",
    version="1.0.0",
    lifespan=lifespan,
    redoc_url=None,
    swagger_ui_parameters={
        "syntaxHighlight.theme": "tomorrow-night",
        "filter": True,
    },
    contact={
        "name": "Sooreoluwa",
    },
    tags_metadata=tags_metadata(),
)



# Custom exception handler for validation errors (422 -> 400)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_details = []
    for error in errors:
        error_details.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg"),
            "type": error.get("type")
        })

    return error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Validation error: Invalid request data",
        data={"errors": error_details},
    )

# Custom exception handler for HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message: str
    data: dict

    if isinstance(exc.detail, dict):
        # If you sometimes raise HTTPException(detail={"message": "...", "data": {...}})
        message = str(exc.detail.get("message", "Request failed"))
        raw_data = exc.detail.get("data", {})
        data = raw_data if isinstance(raw_data, dict) else {"detail": raw_data}
    else:
        message = str(exc.detail) if exc.detail is not None else "Request failed"
        data = {}

    return error_response(
        status_code=exc.status_code,
        message=message,
        data=data,
    )

def custom_openapi():
    if hasattr(app, "openapi_schema") and getattr(app, "openapi_schema", None):
        return getattr(app, "openapi_schema")
    
    openapi_schema = get_openapi(
        title=getattr(app, "title", ""),
        version=getattr(app, "version", ""),
        description=getattr(app, "description", ""),
        routes=getattr(app, "routes", []),
    )
    
    # Remove 422 status codes from all paths
    for path_data in openapi_schema.get("paths", {}).values():
        for method_data in path_data.values():
            if isinstance(method_data, dict) and "responses" in method_data:
                # Remove 422 from responses
                if "422" in method_data["responses"]:
                    del method_data["responses"]["422"]
    
    setattr(app, "openapi_schema", openapi_schema)
    return getattr(app, "openapi_schema")
    
# Set custom OpenAPI schema
app.openapi = custom_openapi

# global router with prefix
api = APIRouter(prefix="/api")

# Include routers
api.include_router(auth.router)
api.include_router(orgs.router)
api.include_router(tools.router)
api.include_router(bookings.router)
api.include_router(vapi_webhooks.router)

# Include routers
app.include_router(api)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_raw_body(request: Request, call_next):
    if get_settings().DEBUG:
        body = await request.body()
        logger.debug(
            "request path={} headers={} body_preview={!r}",
            request.url.path,
            dict(request.headers),
            body[:2000],
        )
    return await call_next(request)
