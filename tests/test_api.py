import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "SentryRouter"


@pytest.mark.asyncio
async def test_chat_completions_mock_route():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "model": "mock-model",
            "messages": [
                {"role": "user", "content": "Hello Router"}
            ]
        }
        response = await ac.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert len(data["choices"]) > 0
    assert "Hello Router" in data["choices"][0]["message"]["content"]
