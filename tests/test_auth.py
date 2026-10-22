from fastapi.testclient import TestClient

from app.main import app

import pytest
from sqlalchemy import text
from app.database import engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    # Runs before every test: wipes test data
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE;"))
    yield


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


def test_login_success():
    client.post(
        "/auth/register",
        json={
            "email": "bob2@gmail.com",
            "password": "bobby123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "bob2@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    client.post(
        "/auth/register",
        json={
            "email": "bob_wrong_pw@gmail.com",
            "password": "bobby123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "bob_wrong_pw@gmail.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_nonexistent_user():
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_get_current_user_success():
    client.post(
        "/auth/register",
        json={
            "email": "bob_wrong_pws@gmail.com",
            "password": "bobby123",
        },
    )

    login_res = client.post(
        "/auth/login",
        data={
            "username": "bob_wrong_pws@gmail.com",
            "password": "bobby123",
        },
    )
    token = login_res.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "bob_wrong_pws@gmail.com"


def test_get_current_user_no_token():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token():
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken123"})
    assert response.status_code == 401