from fastapi.responses import JSONResponse
from app.schemas.responses import ErrorResponse, SuccessResponse
from typing import Any, Optional, Type, TypeVar

T = TypeVar('T')

def responses_example(data_model: Optional[Type[Any]] = None) -> dict:
    return {
        400: {
            "description": "Bad request - validation error or user already exists",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
    
def error_response(message: str, data: Optional[dict] = None, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "isSuccess": False,
            "message": message,
            "data": data if data is not None else {},
        },
    )