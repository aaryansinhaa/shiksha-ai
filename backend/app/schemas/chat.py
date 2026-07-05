from typing import List, Optional
from pydantic import BaseModel, Field

class StartConversationRequest(BaseModel):
    userid: str = Field(..., description="Unique user identifier")
    client: str = Field("web", description="Access client (e.g. web)")
    language: str = Field("en", description="Selected language: 'en' or 'hi'")

class ReplyRequest(BaseModel):
    userid: str = Field(..., description="Unique user identifier")
    client: str = Field("web", description="Access client")
    message: Optional[str] = Field(None, description="User message content")
    user_message: Optional[str] = Field(None, description="User message content")

class ResetConversationRequest(BaseModel):
    userid: str = Field(..., description="Unique user identifier")
    client: str = Field("web", description="Access client")

class ChatMessageItem(BaseModel):
    id: int
    author: str  # "user" or "bot"
    message: str

class ChatMessageResponse(BaseModel):
    message: str
    complete: bool = False
    degraded: bool = False

class ConversationHistoryResponse(BaseModel):
    messages: List[ChatMessageItem] = []
