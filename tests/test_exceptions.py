import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_not_found_exception_structure(client: AsyncClient):
    response = await client.get("/projects/999999/tasks")
    assert response.status_code == 401  # без токена сразу 401

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert data["error"]["message"] == "Not authenticated"


@pytest.mark.asyncio
async def test_validation_error_structure(client: AsyncClient):
    # Отправляем невалидный email при регистрации
    response = await client.post(
        "/auth/register",
        json={"email": "invalid-email-format", "password": "short"},
    )
    assert response.status_code == 422

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["details"] is not None
    assert isinstance(data["error"]["details"], list)
