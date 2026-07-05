from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_async_db
from app.models import User, ConversationState, UserStrategy, InterviewAnswer
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
    raw_dist = {r[0]: r[1] for r in s_res.fetchall()}

    strategy_names = {
        "001-001": "Self-Evaluation",
        "002-001": "Organizing & Transforming",
        "003-001": "Goal Setting & Planning",
        "004-001": "Seeking Information",
        "005-001": "Keeping Records",
        "006-001": "Environmental Structuring",
        "007-001": "Self-Consequences",
        "008-001": "Rehearsing & Memorizing",
        "009-001": "Seeking Social Help (Peers)",
        "009-002": "Seeking Social Help (Teachers)",
        "010-001": "Reviewing Notes",
        "010-002": "Reviewing Tests",
        "010-003": "Reviewing Textbooks",
        "000-000": "Other / Non-SRL"
    }

    formatted_dist = {}
    for code, count in raw_dist.items():
        name = strategy_names.get(code, f"Strategy {code}")
        formatted_dist[f"{code} ({name})"] = count

    # Calculate real average turns
    t_query = select(func.avg(InterviewAnswer.turn))
    t_res = await db.execute(t_query)
    avg_turns = t_res.scalar_one_or_none() or 0.0

    return DashboardStatsResponse(
        total_users=total_users,
        completed_interviews=completed_interviews,
        strategy_distribution=formatted_dist,
        average_turns=round(float(avg_turns), 1)
    )

@router.get("/courses")
async def get_courses(db: AsyncSession = Depends(get_async_db)):
    subjects_query = select(User.study_subject, func.count(User.id)).where(User.study_subject.isnot(None)).group_by(User.study_subject)
    res = await db.execute(subjects_query)
    rows = res.fetchall()

    courses = []
    for idx, r in enumerate(rows):
        courses.append(CourseItem(
            id=f"course_{idx+1}",
            title=r[0] or "General Studies",
            enrolled_students=r[1]
        ))
    return courses
