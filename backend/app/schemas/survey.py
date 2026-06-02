from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class SurveySubmitRequest(BaseModel):
    user_id: str
    user_client: str = "web"
    language: str = "en"
    responses: Dict[str, Any]

class SurveyResultItem(BaseModel):
    strategy_id: str
    name: str
    SU: bool
    SF: float
    SC: float
    RC: float
