import pytest
from sqlalchemy import select
from main import app
from app.database import engine, Base, AsyncSessionLocal
from app.models import User, ConversationState, ConversationCompletedContexts, UserStrategy, StrategyEvaluation
from app.services.state_machine import (
    start_conversation_core, reply_core, calculate_scores, seed_languages_and_contexts
)

@pytest.mark.asyncio
async def test_state_machine_full_workflow():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await seed_languages_and_contexts(db)

        user_id = "test_sm_user"
        client = "web"

        # 1. Start Conversation
        res, status = await start_conversation_core(db, "en", client, user_id)
        assert status == 200
        assert res["complete"] is False
        assert res["current_context"] == 1

        # Verify DB State
        st_res = await db.execute(select(ConversationState).where(ConversationState.id == f"{user_id}:{client}"))
        state = st_res.scalar_one()
        assert state.current_turn == 1
        assert state.current_conversation_step == "intro"
        assert state.probe_count == 0

        # 2. Intro Turn -> Provide Subject
        reply1, status1 = await reply_core(db, client, user_id, "Data Structures & Algorithms")
        assert status1 == 200
        assert reply1["current_context"] == 1
        assert "Scenario 1 of 6" in reply1["message"]

        # Verify step changed to "strategy"
        st_res = await db.execute(select(ConversationState).where(ConversationState.id == f"{user_id}:{client}"))
        state = st_res.scalar_one()
        assert state.current_conversation_step == "strategy"

        # 3. Strategy Turn -> Send Vague Answer ("nothing") -> Triggers PROBE 1
        reply_v1, status_v1 = await reply_core(db, client, user_id, "nothing")
        assert status_v1 == 200
        assert "1 to 5" not in reply_v1["message"]

        st_res = await db.execute(select(ConversationState).where(ConversationState.id == f"{user_id}:{client}"))
        state = st_res.scalar_one()
        assert state.current_conversation_step == "probe"
        assert state.probe_count == 1

        # 4. Probe 1 Turn -> Send Second Vague Answer ("read") -> Triggers PROBE 2
        reply_v2, status_v2 = await reply_core(db, client, user_id, "read")
        assert status_v2 == 200
        assert "1 to 5" not in reply_v2["message"]

        st_res = await db.execute(select(ConversationState).where(ConversationState.id == f"{user_id}:{client}"))
        state = st_res.scalar_one()
        assert state.current_conversation_step == "probe"
        assert state.probe_count == 2

        # 5. Probe 2 Turn -> Send Third Vague Answer ("idk") -> Max probes reached (>=2), defaults to non-SRL (000-000) and advances to frequency step!
        reply_v3, status_v3 = await reply_core(db, client, user_id, "idk")
        assert status_v3 == 200
        assert "1 to 5" in reply_v3["message"] or "rating" in reply_v3["message"]

        st_res = await db.execute(select(ConversationState).where(ConversationState.id == f"{user_id}:{client}"))
        state = st_res.scalar_one()
        assert state.current_conversation_step == "frequency"
        assert state.probe_count == 0

        # 6. Frequency Rating Turn -> Send "4" -> Completes Context 1, advances to Context 2
        reply_f1, status_f1 = await reply_core(db, client, user_id, "4")
        assert status_f1 == 200
        assert reply_f1["current_context"] == 2
        assert reply_f1["completed_count"] == 1

        # Verify ConversationCompletedContexts recorded context 1
        comp_res = await db.execute(select(ConversationCompletedContexts.completed_context_id).where(
            ConversationCompletedContexts.conversation_id == f"{user_id}:{client}"
        ))
        completed_cids = comp_res.scalars().all()
        assert completed_cids == [1]

        # 7. Complete remaining Contexts 2 through 6
        for ctx in range(2, 7):
            # Strategy turn
            await reply_core(db, client, user_id, f"Mind mapping and flashcards for scenario {ctx}")
            # Frequency turn
            f_reply, f_status = await reply_core(db, client, user_id, "5")
            if ctx < 6:
                assert f_reply["complete"] is False
                assert f_reply["completed_count"] == ctx
            else:
                assert f_reply["complete"] is True
                assert f_reply["completed_count"] == 6

        # Verify final interview completed state
        st_res_final = await db.execute(select(ConversationState).where(ConversationState.id == f"{user_id}:{client}"))
        final_state = st_res_final.scalar_one()
        assert final_state.interview_completed is True
        assert final_state.current_conversation_step == "complete"

        # Verify quantitative scores calculated
        eval_res = await db.execute(select(StrategyEvaluation).where(
            StrategyEvaluation.user_id == user_id,
            StrategyEvaluation.user_client == client
        ))
        evals = eval_res.scalars().all()
        assert len(evals) > 0
