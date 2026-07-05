import logging
import json
from typing import Tuple, Dict, Any, Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    User, Language, Context, Strategy, StrategyTranslation,
    ConversationState, InterviewAnswer, UserStrategy, LlmResponse, StrategyEvaluation, ActivityLog
)
from app.services.llm_service import get_llm_response
from app.services.rag_service import match_strategy_rag

logger = logging.getLogger("ShikshaAI.state_machine")

STRATEGY_TAXONOMY_SEED = [
    ("001-001", "Self-Evaluation", "Forethought", "Evaluation", "Evaluating one's own progress, self-testing, checking understanding"),
    ("002-001", "Organizing & Transforming", "Performance", "Task Strategy", "Making outlines, summaries, diagrams, mind maps, reorganizing notes"),
    ("003-001", "Goal Setting & Planning", "Forethought", "Planning", "Setting study goals, scheduling timetables, planning study sessions"),
    ("004-001", "Seeking Information", "Performance", "Information", "Searching library, internet, extra reference materials, online research"),
    ("005-001", "Keeping Records & Monitoring", "Performance", "Monitoring", "Tracking test marks, keeping study logs, recording mistakes"),
    ("006-001", "Environmental Structuring", "Performance", "Environment", "Finding a quiet study space, eliminating distractions, turning off phone"),
    ("007-001", "Self-Consequences", "Performance", "Motivation", "Rewarding oneself after finishing targets, self-punishment/incentives"),
    ("008-001", "Rehearsing & Memorizing", "Performance", "Memorization", "Using flashcards, practice questions, repetition, rote learning"),
    ("009-001", "Seeking Social Assistance (Peers)", "Performance", "Social Help", "Group study with friends, asking classmates for help"),
    ("009-002", "Seeking Social Assistance (Teachers)", "Performance", "Social Help", "Asking professor, instructor, or teacher for clarification"),
    ("010-001", "Reviewing Records (Notes)", "Performance", "Review", "Reviewing lecture notes, class summaries"),
    ("010-002", "Reviewing Records (Tests)", "Performance", "Review", "Solving previous year exam papers, reviewing graded tests"),
    ("010-003", "Reviewing Records (Textbooks)", "Performance", "Review", "Re-reading textbook chapters, reading reference books"),
    ("000-000", "Other / Non-SRL", "Other", "General", "Casual conversation, timepass, non-strategic study statements")
]

async def seed_languages_and_contexts(db: AsyncSession):
    """Seed initial Language, Context, Strategy, StrategyTranslation, and StrategyEmbedding rows if missing."""
    # 1. Seed Languages
    lang_en = await db.get(Language, "en")
    if not lang_en:
        db.add(Language(id="en", lang_code="en"))
    lang_hi = await db.get(Language, "hi")
    if not lang_hi:
        db.add(Language(id="hi", lang_code="hi"))
    await db.flush()

    # 2. Seed Context
    ctx = await db.get(Context, 1)
    if not ctx:
        db.add(Context(id=1, context="Preparing for exams and difficult topics", language_id="en"))
    await db.flush()

    # 3. Seed Strategies, StrategyTranslations & StrategyEmbeddings
    from app.models import StrategyEmbedding
    from app.services.rag_service import _generate_mock_embedding

    for code, name, phase, category, content in STRATEGY_TAXONOMY_SEED:
        strat = await db.get(Strategy, code)
        if not strat:
            db.add(Strategy(id=code))
            await db.flush()
            db.add(StrategyTranslation(id=f"{code}:en", strategy=code, language_id="en", name=name, description=content))
            db.add(StrategyTranslation(id=f"{code}:hi", strategy=code, language_id="hi", name=name, description=content))
        
        # Check StrategyEmbedding
        emb_exists = await db.get(StrategyEmbedding, code)
        if not emb_exists:
            mock_vec = _generate_mock_embedding(f"{name} {content}")
            db.add(StrategyEmbedding(
                strategy_id=code,
                name=name,
                phase=phase,
                category=category,
                content=content,
                embedding=mock_vec
            ))

    await db.commit()

async def get_or_create_user(db: AsyncSession, userid: str, client: str, language: str) -> User:
    """Fetch existing user or create a new user entity with language selection."""
    await seed_languages_and_contexts(db)

    query = select(User).where(User.id == userid, User.client == client)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=userid,
            client=client,
            language_id=language if language in ("en", "hi") else "en",
            study_subject=None,
            context_id="0"
        )
        db.add(user)
        await db.flush()

        conv_state = ConversationState(
            id=f"{userid}:{client}",
            user_id=userid,
            user_client=client,
            interview_completed=False,
            current_turn=0,
            current_context=1,
            current_conversation_step="intro"
        )
        db.add(conv_state)
        await db.commit()
        await db.refresh(user)

    return user

async def start_conversation_core(
    db: AsyncSession, language: str, client: str, userid: str
) -> Tuple[Dict[str, Any], int]:
    """Initialize or reset conversation state for user and generate intro message."""
    user = await get_or_create_user(db, userid, client, language)

    # Load initial prompt based on language
    if language == "hi":
        intro_text = "नमस्ते! शिक्षा AI (Shiksha AI) में आपका स्वागत है। मैं आपका AI अध्ययन सलाहकार हूँ। आप किस विषय की पढ़ाई कर रहे हैं?"
    else:
        intro_text = "Hello! Welcome to Shiksha AI. I am your AI study advisor. What subject are you currently studying?"

    # Reset state if already completed
    if user.conversation_state and user.conversation_state.interview_completed:
        user.conversation_state.interview_completed = False
        user.conversation_state.current_turn = 0
        user.conversation_state.current_context = 1
        user.conversation_state.current_conversation_step = "intro"
        await db.commit()

    turn = (user.conversation_state.current_turn if user.conversation_state else 0) + 1
    if user.conversation_state:
        user.conversation_state.current_turn = turn

    llm_resp = LlmResponse(
        user_id=userid,
        user_client=client,
        message=intro_text,
        context=1,
        turn=turn,
        conversation_step="intro"
    )
    db.add(llm_resp)
    await db.commit()

    return {"message": intro_text}, 200

async def reply_core(
    db: AsyncSession, client: str, userid: str, user_message: str
) -> Tuple[Dict[str, Any], int]:
    """Process incoming user turn through interview state machine."""
    query = select(User).where(User.id == userid, User.client == client)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.conversation_state:
        # Auto-create user session if missing
        user = await get_or_create_user(db, userid, client, "en")

    state = user.conversation_state
    if state.interview_completed:
        return {"message": "साक्षात्कार पूर्ण हो चुका है। / Interview is complete.", "complete": True}, 200

    turn = state.current_turn + 1
    state.current_turn = turn

    # Store user answer
    user_answer = InterviewAnswer(
        user_id=userid,
        user_client=client,
        context=state.current_context,
        turn=turn,
        message=user_message,
        conversation_step=state.current_conversation_step or "intro"
    )
    db.add(user_answer)
    await db.flush()

    current_step = state.current_conversation_step or "intro"
    reply_text = ""
    is_complete = False

    if current_step == "intro":
        user.study_subject = user_message
        state.current_conversation_step = "strategy"
        if user.language_id == "hi":
            reply_text = f"अद्भुत! {user_message} एक महत्वपूर्ण विषय है। जब आप किसी कठिन परीक्षा या अध्याय की तैयारी करते हैं, तो आपकी मुख्य अध्ययन रणनीति क्या होती है?"
        else:
            reply_text = f"Great! {user_message} is a key subject. When you prepare for a challenging exam or topic, what is your primary study strategy?"

    elif current_step == "strategy":
        # RAG Strategy Detection
        candidates = await match_strategy_rag(db, user_message)
        detected_strat = candidates[0]["strategy_id"] if candidates else "000-000"

        user_strat = UserStrategy(
            user_id=userid,
            user_client=client,
            interview_answer_id=user_answer.id,
            context=state.current_context or 1,
            strategy=detected_strat,
            frequency=None
        )
        db.add(user_strat)

        state.current_conversation_step = "frequency"
        state.strategy_for_frequency = detected_strat

        strat_name = candidates[0].get("name", "अध्ययन तकनीक") if candidates else "study method"
        if user.language_id == "hi":
            reply_text = f"धन्यवाद! आपने '{strat_name}' रणनीति का उल्लेख किया। आप इस तकनीक का कितनी बार उपयोग करते हैं? (कृपया 1 से 5 का रेटिंग चुनें: 1 = कभी-कभार, 5 = हमेशा)"
        else:
            reply_text = f"Thank you! You mentioned using '{strat_name}'. How frequently do you apply this technique? (Please select a rating from 1 to 5: 1 = seldom, 5 = always)"

    elif current_step == "frequency":
        try:
            freq_val = int(user_message.strip()[0])
            if freq_val < 1 or freq_val > 5:
                freq_val = 3
        except Exception:
            freq_val = 3

        # Update frequency for recent strategy
        strat_query = select(UserStrategy).where(
            UserStrategy.user_id == userid,
            UserStrategy.user_client == client,
            UserStrategy.context == state.current_context
        ).order_by(UserStrategy.id.desc())
        strat_res = await db.execute(strat_query)
        recent_strat = strat_res.scalars().first()

        if recent_strat:
            recent_strat.frequency = freq_val

        # Move to complete step
        state.current_conversation_step = "complete"
        state.interview_completed = True
        is_complete = True

        # Calculate scores
        await calculate_scores(db, user)

        if user.language_id == "hi":
            reply_text = "साक्षात्कार पूर्ण करने के लिए धन्यवाद! आपकी अध्ययन रणनीति का विश्लेषण किया गया है। आप अपनी व्यक्तिगत रिपोर्ट परिणाम पृष्ठ पर देख सकते हैं।"
        else:
            reply_text = "Thank you for completing the interview! Your study strategy profile has been analyzed. You can review your personalized report on the results page."

    else:
        reply_text = "धन्यवाद! / Thank you!"

    llm_resp = LlmResponse(
        user_id=userid,
        user_client=client,
        message=reply_text,
        context=state.current_context,
        turn=turn,
        conversation_step=current_step
    )
    db.add(llm_resp)
    await db.commit()

    return {"message": reply_text, "complete": is_complete}, 200

async def calculate_scores(db: AsyncSession, user: User) -> List[Dict[str, Any]]:
    """Calculate quantitative SRL scores: SU (Strategy Use), SF (Frequency), SC (Consistency), RC (Relative Consistency)."""
    query = select(UserStrategy).where(UserStrategy.user_id == user.id, UserStrategy.user_client == user.client)
    res = await db.execute(query)
    strategies = res.scalars().all()

    eval_map = {}
    for s in strategies:
        sid = s.strategy
        if sid not in eval_map:
            eval_map[sid] = {"SF": 0, "SC": 0}
        eval_map[sid]["SF"] += 1
        eval_map[sid]["SC"] += (s.frequency or 3)

    results = []
    for sid, data in eval_map.items():
        su = data["SF"] > 0
        sf = float(data["SF"])
        sc = float(data["SC"])
        
        evaluation = StrategyEvaluation(
            user_id=user.id,
            user_client=user.client,
            strategy=sid,
            SU=su,
            SF=sf,
            SC=sc
        )
        db.add(evaluation)
        results.append({
            "strategy_id": sid,
            "SU": su,
            "SF": sf,
            "SC": sc,
            "RC": sc / sf if sf > 0 else 0.0
        })

    await db.commit()
    return results
