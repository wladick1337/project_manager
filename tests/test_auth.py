from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_register_user_success():
    response = client.post(
        "/auth/register",
        json={
            "email": "bob@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "bob@gmail.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email():
    response = client.post(
        "/auth/register",
        json={
            "email": "bob1@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/auth/register",
        json={
            "email": "bob1@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Email already registered"