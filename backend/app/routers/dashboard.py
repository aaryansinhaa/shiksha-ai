from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from app.database import get_async_db
from app.models import User, ConversationState, UserStrategy, InterviewAnswer, LlmResponse, StrategyEvaluation, MouseTrace, ActivityLog
from app.schemas.dashboard import DashboardStatsResponse, CourseItem

router = APIRouter(tags=["Dashboard & Analytics"])

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
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

    t_query = select(func.avg(InterviewAnswer.turn))
    t_res = await db.execute(t_query)
    avg_turns = t_res.scalar_one_or_none() or 0.0

    return DashboardStatsResponse(
        total_users=total_users,
        completed_interviews=completed_interviews,
        strategy_distribution=formatted_dist,
        average_turns=round(float(avg_turns), 1)
    )

@router.get("/dashboard/courses")
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

@router.get("/student/evaluations")
async def get_student_evaluations(
    userid: str = Query(...),
    client: str = Query("web"),
    db: AsyncSession = Depends(get_async_db)
):
    query = select(StrategyEvaluation).where(
        StrategyEvaluation.user_id == userid,
        StrategyEvaluation.user_client == client
    )
    res = await db.execute(query)
    evals = res.scalars().all()

    strategy_names = {
        "001-001": "Self-Evaluation",
        "002-001": "Organizing & Transforming",
        "003-001": "Goal Setting & Planning",
        "004-001": "Seeking Information",
        "005-001": "Keeping Records & Monitoring",
        "006-001": "Environmental Structuring",
        "007-001": "Self-Consequences",
        "008-001": "Rehearsing & Memorizing",
        "009-001": "Seeking Social Assistance (Peers)",
        "009-002": "Seeking Social Assistance (Teachers)",
        "010-001": "Reviewing Records (Notes)",
        "010-002": "Reviewing Records (Tests)",
        "010-003": "Reviewing Records (Textbooks)",
        "000-000": "Other / Non-SRL"
    }

    out = []
    for item in evals:
        out.append({
            "strategy_id": item.strategy,
            "strategy_name": strategy_names.get(item.strategy, item.strategy),
            "SU": item.SU,
            "SF": item.SF,
            "SC": item.SC,
            "RC": round(item.SC / item.SF, 1) if item.SF > 0 else 0.0
        })
    return out

@router.get("/researcher/students")
async def get_all_students(db: AsyncSession = Depends(get_async_db)):
    """Fetch saved information of all students, their study subjects, turn counts, and transcripts."""
    users_query = select(User)
    u_res = await db.execute(users_query)
    users = u_res.scalars().all()

    output = []
    for u in users:
        # Fetch conversation state
        st_query = select(ConversationState).where(ConversationState.user_id == u.id, ConversationState.user_client == u.client)
        st_res = await db.execute(st_query)
        st = st_res.scalar_one_or_none()

        # Fetch answers
        ans_query = select(InterviewAnswer).where(InterviewAnswer.user_id == u.id, InterviewAnswer.user_client == u.client).order_by(InterviewAnswer.turn.asc())
        ans_res = await db.execute(ans_query)
        answers = ans_res.scalars().all()

        # Fetch LLM responses
        llm_query = select(LlmResponse).where(LlmResponse.user_id == u.id, LlmResponse.user_client == u.client).order_by(LlmResponse.turn.asc())
        llm_res = await db.execute(llm_query)
        llm_responses = llm_res.scalars().all()

        transcript = []
        max_turns = max(len(answers), len(llm_responses))
        for t in range(max_turns):
            if t < len(llm_responses):
                transcript.append({"role": "model", "text": llm_responses[t].message, "turn": llm_responses[t].turn})
            if t < len(answers):
                transcript.append({"role": "user", "text": answers[t].message, "turn": answers[t].turn})

        output.append({
            "user_id": u.id,
            "client": u.client,
            "language": u.language_id,
            "study_subject": u.study_subject or "Not specified",
            "completed": st.interview_completed if st else False,
            "total_turns": st.current_turn if st else 0,
            "completed_contexts_count": len(st.completed_contexts) if (st and hasattr(st, 'completed_contexts') and st.completed_contexts) else (6 if (st and st.interview_completed) else 0),
            "transcript": transcript
        })
    return output

@router.get("/researcher/telemetry")
async def get_telemetry_logs(db: AsyncSession = Depends(get_async_db)):
    """Fetch live sampled mouse trace points and activity event logs from PostgreSQL."""
    m_query = select(MouseTrace).order_by(MouseTrace.id.desc()).limit(100)
    m_res = await db.execute(m_query)
    traces = m_res.scalars().all()

    a_query = select(ActivityLog).order_by(ActivityLog.id.desc()).limit(50)
    a_res = await db.execute(a_query)
    activities = a_res.scalars().all()

    trace_data = []
    for t in traces:
        trace_data.append({
            "id": t.id,
            "user_id": t.user_id,
            "session_id": t.session_id,
            "x": t.x,
            "y": t.y,
            "page_width": t.page_width,
            "page_height": t.page_height,
            "timestamp": t.timestamp
        })

    activity_data = []
    for act in activities:
        activity_data.append({
            "id": act.id,
            "user_id": act.user_id,
            "action": act.action,
            "value": act.value,
            "timestamp": act.timestamp
        })

    return {
        "mouse_traces": trace_data,
        "activity_logs": activity_data
    }
