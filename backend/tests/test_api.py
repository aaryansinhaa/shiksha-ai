import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.database import engine, Base, AsyncSessionLocal
from sqlalchemy import select
from app.models import ConversationCompletedContexts, ConversationState

@pytest.mark.asyncio
async def test_health_and_protocols():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/protocols")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

@pytest.mark.asyncio
async def test_start_conversation():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "userid": "test_user_123",
            "client": "web",
            "language": "hi"
        }
        response = await client.post("/startConversation", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "शिक्षा AI" in data["message"] or "Shiksha AI" in data["message"]
        assert data["current_context"] == 1
        assert data["total_contexts"] == 6

@pytest.mark.asyncio
async def test_multi_context_interview_loop():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = "test_loop_user"
    client_id = "web"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Start Conversation
        start_resp = await client.post("/startConversation", json={
            "userid": user_id,
            "client": client_id,
            "language": "en"
        })
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        assert start_data["complete"] is False

        # 2. Intro Step - Send subject
        reply1 = await client.post("/reply", json={
            "userid": user_id,
            "client": client_id,
            "message": "Physics"
        })
        assert reply1.status_code == 200
        d1 = reply1.json()
        assert d1["complete"] is False
        assert d1["current_context"] == 1
        assert "Scenario 1 of 6" in d1["message"]

        # 3. Loop through 6 contexts (strategy -> frequency)
        for ctx_id in range(1, 7):
            # Strategy turn
            strat_resp = await client.post("/reply", json={
                "userid": user_id,
                "client": client_id,
                "message": f"Strategy for scenario {ctx_id}: I outline and practice questions."
            })
            assert strat_resp.status_code == 200
            sd = strat_resp.json()
            assert sd["complete"] is False
            assert "1 to 5" in sd["message"] or "rating" in sd["message"]

            # Frequency turn
            freq_resp = await client.post("/reply", json={
                "userid": user_id,
                "client": client_id,
                "message": "4"
            })
            assert freq_resp.status_code == 200
            fd = freq_resp.json()

            if ctx_id < 6:
                assert fd["complete"] is False
                assert fd["current_context"] == ctx_id + 1
                assert f"Scenario ({ctx_id + 1} of 6)" in fd["message"] or f"Scenario {ctx_id + 1} of 6" in fd["message"] or "Next scenario" in fd["message"]
            else:
                assert fd["complete"] is True
                assert "completing the interview" in fd["message"] or "Thank you" in fd["message"]

    # 4. Database Verification
    async with AsyncSessionLocal() as db:
        conv_id = f"{user_id}:{client_id}"
        q = select(ConversationCompletedContexts.completed_context_id).where(
            ConversationCompletedContexts.conversation_id == conv_id
        ).order_by(ConversationCompletedContexts.completed_context_id)
        res = await db.execute(q)
        completed_cids = res.scalars().all()
        assert completed_cids == [1, 2, 3, 4, 5, 6]
