from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class TripCreate(BaseModel):
    brief: str


class ChangeRequest(BaseModel):
    change_request: str


class TripResponse(BaseModel):
    id: str
    brief: str
    status: str
    itinerary: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StreamMessage(BaseModel):
    type: str  # status | tool_call | tool_result | complete | error
    message: Optional[str] = None
    tool: Optional[str] = None
    summary: Optional[str] = None
    itinerary: Optional[Any] = None
