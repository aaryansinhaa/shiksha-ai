from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_async_db
from app.models import User, ConversationState, UserStrategy
from app.schemas.dashboard import DashboardStatsResponse, CourseItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_async_db)):
    u_count = await db.execute(select(func.count(User.id.distinct())))
    total_users = u_count.scalar_one_or_none() or 0

    c_count = await db.execute(select(func.count(ConversationState.id)).where(ConversationState.interview_completed == True))
    completed_interviews = c_count.scalar_one_or_none() or 0

    s_query = select(UserStrategy.strategy, func.count(UserStrategy.id)).group_by(UserStrategy.strategy)
    s_res = await db.execute(s_query)
    dist = {r[0]: r[1] for r in s_res.fetchall()}

    return DashboardStatsResponse(
        total_users=total_users,
        completed_interviews=completed_interviews,
        strategy_distribution=dist,
        average_turns=4.5
    )

@router.get("/courses")
async def get_courses(db: AsyncSession = Depends(get_async_db)):
    return [
        CourseItem(id="cs101", title="Computer Science & AI Fundamentals", enrolled_students=45),
        CourseItem(id="edu201", title="Educational Psychology & Learning Design", enrolled_students=32)
    ]
