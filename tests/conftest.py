import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.database import engine
from app.main import app


@pytest.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as connection:
        # Чистим все связанные таблицы сразу
        await connection.execute(
            text("TRUNCATE TABLE tasks, projects, users RESTART IDENTITY CASCADE;")
        )
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers(client):
    async def _get(email: str = "test@example.com", password: str = "password123"):
        await client.post("/auth/register", json={"email": email, "password": password})
        login_res = await client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _get
