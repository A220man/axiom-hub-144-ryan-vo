import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "axiom-hub"

@pytest.mark.asyncio
async def test_version():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.1.0"
        assert data["name"] == "axiom-hub-144-ryan-vo"
