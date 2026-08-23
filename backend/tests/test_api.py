import pytest
import json
from httpx import AsyncClient, ASGITransport
from main import app
from app.database import engine, Base, AsyncSessionLocal
from sqlalchemy import select
from app.models import ConversationCompletedContexts, ConversationState, UserStrategy, StrategyEvaluation, User, Archive, InterviewAnswer, LlmResponse, ActivityLog
from app.services.state_machine import calculate_scores

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

@pytest.mark.asyncio
async def test_probe_state_and_clarification_limit():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = "test_probe_user"
    client_id = "web"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Start & send subject
        await client.post("/startConversation", json={"userid": user_id, "client": client_id, "language": "en"})
        await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "Chemistry"})

        # Scenario 1 - Send vague answer "nothing" -> Triggers PROBE 1
        p1_resp = await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "nothing"})
        assert p1_resp.status_code == 200
        p1_data = p1_resp.json()
        assert p1_data["complete"] is False
        assert "1 to 5" not in p1_data["message"]  # Should NOT skip to rating
        assert any(w in p1_data["message"].lower() for w in ["elaborate", "specific", "technique", "action", "detail", "could you"])

        # Probe 1 Response - Send specific strategy -> Transitions to Frequency rating
        strat_resp = await client.post("/reply", json={
            "userid": user_id,
            "client": client_id,
            "message": "I make flashcards and practice previous year test questions."
        })
        assert strat_resp.status_code == 200
        s_data = strat_resp.json()
        assert "1 to 5" in s_data["message"] or "rating" in s_data["message"]

        # Send frequency rating -> Advances to Scenario 2
        f_resp = await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "5"})
        assert f_resp.status_code == 200
        assert f_resp.json()["current_context"] == 2

        # Scenario 2 - Test 2-probe limit with repeated vague answers
        # Turn 1: Vague answer -> Probe 1
        probe1 = await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "just study"})
        assert "1 to 5" not in probe1.json()["message"]

        # Turn 2: Vague answer -> Probe 2
        probe2 = await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "read"})
        assert "1 to 5" not in probe2.json()["message"]

        # Turn 3: Vague answer -> Probe limit reached (>= 2), defaults to non-SRL and transitions to frequency rating!
        limit_resp = await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "idk"})
        assert limit_resp.status_code == 200
        l_data = limit_resp.json()
        assert "1 to 5" in l_data["message"] or "rating" in l_data["message"]

@pytest.mark.asyncio
async def test_user_strategy_ordering_and_score_deduplication():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = "test_dedup_user"
    client_id = "web"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Start & set subject
        await client.post("/startConversation", json={"userid": user_id, "client": client_id, "language": "en"})
        await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "Computer Science"})

        # Complete all 6 scenarios
        for c in range(1, 7):
            await client.post("/reply", json={"userid": user_id, "client": client_id, "message": f"Flashcards and outline notes for context {c}"})
            await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "4"})

    async with AsyncSessionLocal() as db:
        # 1. Verify UserStrategy rows have created_at populated
        us_q = select(UserStrategy).where(UserStrategy.user_id == user_id, UserStrategy.user_client == client_id)
        us_res = await db.execute(us_q)
        user_strats = us_res.scalars().all()
        assert len(user_strats) > 0
        for s in user_strats:
            assert s.created_at is not None

        # 2. Verify StrategyEvaluation contains no duplicate strategy entries
        eval_q = select(StrategyEvaluation).where(StrategyEvaluation.user_id == user_id, StrategyEvaluation.user_client == client_id)
        eval_res = await db.execute(eval_q)
        evals = eval_res.scalars().all()
        strategy_ids = [e.strategy for e in evals]
        assert len(strategy_ids) == len(set(strategy_ids))  # Zero duplicates

        # 3. Call calculate_scores again and verify no duplicate evaluations created
        u_q = select(User).where(User.id == user_id, User.client == client_id)
        u_res = await db.execute(u_q)
        user = u_res.scalar_one()

        await calculate_scores(db, user)

        eval_res2 = await db.execute(eval_q)
        evals2 = eval_res2.scalars().all()
        strategy_ids2 = [e.strategy for e in evals2]
        assert len(strategy_ids2) == len(set(strategy_ids2))  # Still zero duplicates
        assert len(evals2) == len(evals)  # Count did not inflate

@pytest.mark.asyncio
async def test_reset_conversation_archiving_and_cleanup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = "test_reset_archive_user"
    client_id = "web"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Start & send turns
        await client.post("/startConversation", json={"userid": user_id, "client": client_id, "language": "en"})
        await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "Mathematics"})
        await client.post("/reply", json={"userid": user_id, "client": client_id, "message": "I solve previous year papers and outline formulas."})

        # 2. Call /resetConversation
        reset_resp = await client.post("/resetConversation", json={"userid": user_id, "client": client_id})
        assert reset_resp.status_code == 200
        assert "archived and reset" in reset_resp.json()["message"] or "reset" in reset_resp.json()["message"]

        # 3. Verify /conversation returns clean slate
        conv_resp = await client.get(f"/conversation?userid={user_id}&client={client_id}")
        assert conv_resp.status_code == 200
        assert conv_resp.json()["messages"] == []

    # 4. Database Verification
    async with AsyncSessionLocal() as db:
        # Verify archive table has entry
        arc_q = select(Archive).where(Archive.user_id == user_id, Archive.user_client == client_id)
        arc_res = await db.execute(arc_q)
        archives = arc_res.scalars().all()
        assert len(archives) == 1
        archived_data = json.loads(archives[0].archived_conversation)
        assert len(archived_data) > 0

        # Verify active tables are cleared
        ans_res = await db.execute(select(InterviewAnswer).where(InterviewAnswer.user_id == user_id, InterviewAnswer.user_client == client_id))
        assert len(ans_res.scalars().all()) == 0

        llm_res = await db.execute(select(LlmResponse).where(LlmResponse.user_id == user_id, LlmResponse.user_client == client_id))
        assert len(llm_res.scalars().all()) == 0

        strat_res = await db.execute(select(UserStrategy).where(UserStrategy.user_id == user_id, UserStrategy.user_client == client_id))
        assert len(strat_res.scalars().all()) == 0

        # Verify ConversationState reset
        st_res = await db.execute(select(ConversationState).where(ConversationState.id == f"{user_id}:{client_id}"))
        state = st_res.scalar_one()
        assert state.current_turn == 0
        assert state.current_context == 1
        assert state.interview_completed is False
        assert state.current_conversation_step == "intro"

@pytest.mark.asyncio
async def test_telemetry_timestamps_and_tab_events():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = "test_telemetry_user"
    client_id = "web"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test /log/interaction without explicit timestamp -> Should save real epoch ms (> 1_000_000_000_000, not hardcoded 1000!)
        resp1 = await client.post("/log/interaction", json={
            "user_id": user_id,
            "user_client": client_id,
            "action": "click_button",
            "step": "intro"
        })
        assert resp1.status_code == 200

        # 2. Test /log/tab_event for tab_blur and tab_focus
        resp2 = await client.post("/log/tab_event", json={
            "user_id": user_id,
            "user_client": client_id,
            "event_type": "tab_blur",
            "timestamp": 1700000000000
        })
        assert resp2.status_code == 200

    async with AsyncSessionLocal() as db:
        # Query ActivityLog rows
        q = select(ActivityLog).where(ActivityLog.user_id == user_id, ActivityLog.user_client == client_id)
        res = await db.execute(q)
        logs = res.scalars().all()
        assert len(logs) == 2

        interaction_log = next(l for l in logs if l.action == "click_button")
        assert interaction_log.timestamp > 1_000_000_000_000  # Valid epoch ms, NOT 1000!

        tab_log = next(l for l in logs if "tab_blur" in l.action or l.step == "tab_blur")
        assert tab_log.timestamp == 1700000000000

@pytest.mark.asyncio
async def test_protocol_crud_export_import():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /protocols -> List (ensure interview_default exists)
        list_resp = await client.get("/protocols")
        assert list_resp.status_code == 200
        protos = list_resp.json()
        assert len(protos) >= 1
        assert any(p["name"] == "zimmerman_14_taxon_srl_protocol" for p in protos)

        # 2. POST /protocols -> Create custom protocol
        new_proto = {
            "name": "test_protocol_01",
            "title": "Test Custom Protocol",
            "languages": ["en", "hi"],
            "steps": [{"id": "s1", "type": "scenario"}]
        }
        create_resp = await client.post("/protocols", json=new_proto)
        assert create_resp.status_code == 201
        assert create_resp.json()["name"] == "test_protocol_01"

        # 3. GET /protocols/test_protocol_01 -> Retrieve
        get_resp = await client.get("/protocols/test_protocol_01")
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Test Custom Protocol"

        # 4. PUT /protocols/test_protocol_01 -> Update
        update_resp = await client.put("/protocols/test_protocol_01", json={"title": "Updated Custom Protocol"})
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Updated Custom Protocol"

        # 5. GET /protocols/test_protocol_01/export -> Export JSON
        export_resp = await client.get("/protocols/test_protocol_01/export")
        assert export_resp.status_code == 200
        assert "attachment;" in export_resp.headers.get("content-disposition", "")
        export_data = export_resp.json()
        assert export_data["name"] == "test_protocol_01"
        assert export_data["title"] == "Updated Custom Protocol"

        # 6. POST /protocols/import -> Import payload
        import_proto = {
            "name": "imported_protocol_01",
            "title": "Imported Test Protocol",
            "languages": ["en"],
            "steps": [{"id": "imp1"}]
        }
        import_resp = await client.post("/protocols/import", json=import_proto)
        assert import_resp.status_code == 200
        assert import_resp.json()["name"] == "imported_protocol_01"

        # 7. DELETE /protocols/test_protocol_01 -> Delete
        del_resp = await client.delete("/protocols/test_protocol_01")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        # Verify deleted
        get_del = await client.get("/protocols/test_protocol_01")
        assert get_del.status_code == 404
