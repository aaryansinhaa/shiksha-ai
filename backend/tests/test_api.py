import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.database import engine, Base

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
