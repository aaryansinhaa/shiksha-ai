from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_db
from app.models import SurveyResponse, StrategyEvaluation
from app.schemas.survey import SurveySubmitRequest, SurveyResultItem

router = APIRouter(tags=["Survey"])

@router.get("/survey/{survey_id}")
async def get_survey_definition(survey_id: str):
    return {
        "survey_id": survey_id,
        "title": "SRL-O Student Self-Regulated Learning Assessment",
        "items": [
            {"id": "q1", "text": "I set clear goals before studying.", "type": "likert"},
            {"id": "q2", "text": "I make summary notes or mind maps.", "type": "likert"},
            {"id": "q3", "text": "I eliminate distractions like phone notifications.", "type": "likert"}
        ]
    }

@router.post("/survey/{survey_id}/submit")
async def submit_survey(
    survey_id: str,
    payload: SurveySubmitRequest,
    db: AsyncSession = Depends(get_async_db)
):
    resp = SurveyResponse(
        survey_id=survey_id,
        user_id=payload.user_id,
        user_client=payload.user_client,
        language=payload.language,
        responses=payload.responses
    )
    db.add(resp)
    await db.commit()
    return {"status": "submitted", "survey_id": survey_id}

@router.get("/student/results")
async def get_student_results(
    userid: str,
    client: str = "web",
    db: AsyncSession = Depends(get_async_db)
):
    query = select(StrategyEvaluation).where(
        StrategyEvaluation.user_id == userid, StrategyEvaluation.user_client == client
    )
    res = await db.execute(query)
    evals = res.scalars().all()

    results = []
    for e in evals:
        rc = (e.SC / e.SF) if e.SF > 0 else 0.0
        results.append(SurveyResultItem(
            strategy_id=e.strategy,
            name=f"Strategy {e.strategy}",
            SU=e.SU,
            SF=e.SF,
            SC=e.SC,
            RC=rc
        ))
    return {"results": results}
