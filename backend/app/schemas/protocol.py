from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ProtocolSchema(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    steps: List[Dict[str, Any]] = []

class ProtocolResponse(BaseModel):
    name: str
    protocol: Dict[str, Any]
