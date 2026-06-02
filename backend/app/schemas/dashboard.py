from typing import Dict, List, Any
from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    total_users: int = 0
    completed_interviews: int = 0
    strategy_distribution: Dict[str, int] = {}
    average_turns: float = 0.0

class CourseItem(BaseModel):
    id: str
    title: str
    enrolled_students: int = 0
