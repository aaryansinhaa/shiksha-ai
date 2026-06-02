from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MouseTraceItem(BaseModel):
    x: int
    y: int
    page_width: Optional[int] = None
    page_height: Optional[int] = None
    timestamp: Optional[int] = None

class MouseTraceBatchRequest(BaseModel):
    user_id: Optional[str] = None
    user_client: Optional[str] = "web"
    session_id: Optional[str] = None
    traces: List[MouseTraceItem] = []

class TabEventRequest(BaseModel):
    user_id: Optional[str] = None
    user_client: Optional[str] = "web"
    event_type: str = Field(..., description="e.g. tab_focus or tab_blur")
    timestamp: int

class InteractionLogRequest(BaseModel):
    user_id: Optional[str] = None
    user_client: Optional[str] = "web"
    action: str
    value: Optional[Dict[str, Any]] = None
    context: Optional[str] = None
    strategy: Optional[str] = None
    step: Optional[str] = None
