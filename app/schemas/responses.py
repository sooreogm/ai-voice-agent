from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field, model_validator
from collections import OrderedDict

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    isSuccess: bool = Field(description="Indicates if the request was successful")
    message: str = Field(description="Response message")
    data: T = Field(description="Response data payload")  # Made required - no Optional/None

    @model_validator(mode='after')
    def validate_data_not_none(self):
        """Ensure data is not None"""
        if self.data is None:
            raise ValueError("data must be provided and cannot be None")
        return self

    class Config:
        # Removed static example - FastAPI will use examples from nested schema types
        # For example, APIResponse[AuthResponse] will use AuthResponse's example
        pass

class ErrorResponse(BaseModel):
    """Standard error response"""
    isSuccess: bool = Field(False, description="Always false for error responses")
    message: str = Field(description="Error message")
    data: Optional[Any] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
             "example": OrderedDict([
                ("isSuccess", False),
                ("message","Error message"),
                ("data", None)
            ])
        }
