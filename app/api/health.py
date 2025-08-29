"""
Health check endpoints.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict

router = APIRouter()


class HealthStatusOutput(BaseModel):

    status: str


@router.get(
    "/health", status_code=status.HTTP_200_OK, response_model=HealthStatusOutput
)
async def health_check() -> Dict:
    """Health check endpoint."""
    return {"status": "healthy"}
