# Custom OpenAPI schema to remove 422 from all endpoints
from typing import Any

def tags_metadata() -> Any:
    return [
        {
            "name": "Tools",
            "description": "Tools for AI Voice Agent",
        }
    ]