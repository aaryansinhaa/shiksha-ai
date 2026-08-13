from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class ProtocolCreate(BaseModel):
    name: str
    title: str
    languages: List[str] = ["en", "hi"]
    steps: List[Dict[str, Any]]

class ProtocolUpdate(BaseModel):
    title: Optional[str] = None
    languages: Optional[List[str]] = None
    steps: Optional[List[Dict[str, Any]]] = None

class ProtocolResponse(BaseModel):
    name: str
    title: str
    languages: List[str]
    steps: Any
