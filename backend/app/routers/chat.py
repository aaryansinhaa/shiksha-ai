from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_db
from app.schemas.chat import (
    StartConversationRequest, ReplyRequest, ResetConversationRequest,
    ChatMessageResponse, ConversationHistoryResponse, ChatMessageItem
)
from app.services.state_machine import start_conversation_core, reply_core
from app.models import InterviewAnswer, LlmResponse

router = APIRouter(prefix="", tags=["Chat"])

@router.post("/startConversation", response_model=ChatMessageResponse)
async def start_conversation(
    payload: StartConversationRequest,
    db: AsyncSession = Depends(get_async_db)
):
    resp, status_code = await start_conversation_core(
        db, payload.language, payload.client, payload.userid
    )
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=resp)
    return ChatMessageResponse(
        message=resp["message"],
        complete=resp.get("complete", False),
        current_context=resp.get("current_context"),
        total_contexts=resp.get("total_contexts"),
        completed_count=resp.get("completed_count")
    )

@router.post("/reply", response_model=ChatMessageResponse)
async def reply(
    payload: ReplyRequest,
    db: AsyncSession = Depends(get_async_db)
):
    msg = payload.message or payload.user_message or ""
    resp, status_code = await reply_core(
        db, payload.client, payload.userid, msg
    )
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=resp.get("error", "Reply failed"))
    return ChatMessageResponse(
        message=resp.get("message", ""),
        complete=resp.get("complete", False),
        current_context=resp.get("current_context"),
        total_contexts=resp.get("total_contexts"),
        completed_count=resp.get("completed_count")
    )

@router.post("/resetConversation")
async def reset_conversation(
    payload: ResetConversationRequest,
    db: AsyncSession = Depends(get_async_db)
):
    # Reset conversation handler
    return {"message": "Conversation has been reset successfully."}

@router.get("/conversation", response_model=ConversationHistoryResponse)
async def get_conversation(
    userid: str,
    client: str = "web",
    db: AsyncSession = Depends(get_async_db)
):
    user_q = select(InterviewAnswer).where(
        InterviewAnswer.user_id == userid, InterviewAnswer.user_client == client
    )
    bot_q = select(LlmResponse).where(
        LlmResponse.user_id == userid, LlmResponse.user_client == client
    )

    user_res = await db.execute(user_q)
    bot_res = await db.execute(bot_q)

    user_rows = user_res.scalars().all()
    bot_rows = bot_res.scalars().all()

    combined = []
    for r in user_rows:
        combined.append({"turn": r.turn, "author": "user", "message": r.message, "time": r.message_time})
    for r in bot_rows:
        combined.append({"turn": r.turn, "author": "bot", "message": r.message, "time": r.message_time})

    combined.sort(key=lambda x: (x["turn"], 0 if x["author"] == "user" else 1))

    items = [
        ChatMessageItem(id=i + 1, author=c["author"], message=c["message"])
        for i, c in enumerate(combined)
    ]
    return ConversationHistoryResponse(messages=items)
