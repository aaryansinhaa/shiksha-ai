from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.schemas.log import MouseTraceBatchRequest, TabEventRequest, InteractionLogRequest
from app.models import MouseTrace, ActivityLog

router = APIRouter(prefix="/log", tags=["Logging"])

@router.post("/mouse_traces")
async def log_mouse_traces(
    payload: MouseTraceBatchRequest,
    db: AsyncSession = Depends(get_async_db)
):
    for item in payload.traces:
        trace = MouseTrace(
            user_id=payload.user_id,
            user_client=payload.user_client,
            session_id=payload.session_id,
            x=item.x,
            y=item.y,
            page_width=item.page_width,
            page_height=item.page_height,
            timestamp=item.timestamp
        )
        db.add(trace)
    await db.commit()
    return {"status": "success", "count": len(payload.traces)}

@router.post("/tab_event")
async def log_tab_event(
    payload: TabEventRequest,
    db: AsyncSession = Depends(get_async_db)
):
    log_entry = ActivityLog(
        user_id=payload.user_id,
        user_client=payload.user_client,
        action=f"tab_event_{payload.event_type}",
        timestamp=payload.timestamp
    )
    db.add(log_entry)
    await db.commit()
    return {"status": "success"}

@router.post("/interaction")
async def log_interaction(
    payload: InteractionLogRequest,
    db: AsyncSession = Depends(get_async_db)
):
    log_entry = ActivityLog(
        user_id=payload.user_id,
        user_client=payload.user_client,
        action=payload.action,
        value=payload.value,
        context=payload.context,
        strategy=payload.strategy,
        step=payload.step,
        timestamp=1000
    )
    db.add(log_entry)
    await db.commit()
    return {"status": "success"}
