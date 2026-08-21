import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.database import engine, Base, AsyncSessionLocal

@pytest.mark.asyncio
async def test_dashboard_router():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /researcher/students
        resp1 = await client.get("/researcher/students")
        assert resp1.status_code == 200
        assert isinstance(resp1.json(), list)

        # 2. GET /student/evaluations
        resp2 = await client.get("/student/evaluations?userid=test_user&client=web")
        assert resp2.status_code == 200
        assert isinstance(resp2.json(), list)

        # 3. GET /dashboard/stats
        resp3 = await client.get("/dashboard/stats")
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert "total_users" in data3
        assert "completed_interviews" in data3

@pytest.mark.asyncio
async def test_log_router():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. POST /log/mouse_traces
        mouse_payload = {
            "user_id": "test_log_user",
            "user_client": "web",
            "session_id": "s1",
            "traces": [
                {"x": 100, "y": 200, "page_width": 1920, "page_height": 1080, "timestamp": 1700000000000}
            ]
        }
        resp1 = await client.post("/log/mouse_traces", json=mouse_payload)
        assert resp1.status_code == 200
        assert resp1.json()["count"] == 1

        # 2. POST /log/tab_event
        tab_payload = {
            "user_id": "test_log_user",
            "user_client": "web",
            "event_type": "tab_focus",
            "timestamp": 1700000001000
        }
        resp2 = await client.post("/log/tab_event", json=tab_payload)
        assert resp2.status_code == 200

        # 3. POST /log/interaction
        interaction_payload = {
            "user_id": "test_log_user",
            "user_client": "web",
            "action": "button_click",
            "step": "strategy"
        }
        resp3 = await client.post("/log/interaction", json=interaction_payload)
        assert resp3.status_code == 200

@pytest.mark.asyncio
async def test_survey_router():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /survey/{survey_id}
        resp1 = await client.get("/survey/srl_post_survey")
        assert resp1.status_code == 200
        assert resp1.json()["survey_id"] == "srl_post_survey"

        # 2. POST /survey/{survey_id}/submit
        survey_payload = {
            "user_id": "test_survey_user",
            "user_client": "web",
            "language": "en",
            "responses": {"q1": 5, "q2": 4}
        }
        resp2 = await client.post("/survey/srl_post_survey/submit", json=survey_payload)
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "submitted"

        # 3. GET /student/results
        resp3 = await client.get("/student/results?userid=test_survey_user&client=web")
        assert resp3.status_code == 200
        assert "results" in resp3.json()

@pytest.mark.asyncio
async def test_protocol_router_full_lifecycle():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. List protocols
        list_resp = await client.get("/protocols")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        # 2. Create protocol
        proto_name = "test_router_proto"
        create_payload = {
            "name": proto_name,
            "title": "Test Router Protocol",
            "languages": ["en", "hi"],
            "steps": [{"id": "s1", "type": "open_question"}]
        }
        c_resp = await client.post("/protocols", json=create_payload)
        assert c_resp.status_code == 201
        assert c_resp.json()["name"] == proto_name

        # 3. Retrieve protocol
        g_resp = await client.get(f"/protocols/{proto_name}")
        assert g_resp.status_code == 200
        assert g_resp.json()["title"] == "Test Router Protocol"

        # 4. Update protocol
        u_resp = await client.put(f"/protocols/{proto_name}", json={"title": "Updated Title"})
        assert u_resp.status_code == 200
        assert u_resp.json()["title"] == "Updated Title"

        # 5. Export protocol
        ex_resp = await client.get(f"/protocols/{proto_name}/export")
        assert ex_resp.status_code == 200
        assert ex_resp.json()["name"] == proto_name

        # 6. Delete protocol
        d_resp = await client.delete(f"/protocols/{proto_name}")
        assert d_resp.status_code == 200
        assert d_resp.json()["status"] == "deleted"
