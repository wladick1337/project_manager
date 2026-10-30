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

# 1. Функция-помощник: регистрирует юзера и сразу отдаёт готовый заголовок с токеном
def get_auth_headers(email: str, password: str = "password123") -> dict[str, str]:
    # Регистрация
    client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    # Логин
    login_res = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    token = login_res.json()["access_token"]
    # Возвращаем заголовок, который требует FastAPI
    return {"Authorization": f"Bearer {token}"}


def test_task_lifecycle():
    headers = get_auth_headers("test123@gmail.com")

    create_project = client.post(
        "/projects",
        json={"title": "My First Project", "description": "Testing FastAPI"},
        headers=headers,
    )

    assert create_project.status_code == 201
    project_id = create_project.json()["id"]

    create_task = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers,
    )

    assert create_task.status_code == 201
    task_data = create_task.json()
    assert task_data["title"] == "My First Task"
    assert "id" in task_data

    task_id = task_data["id"]

    get_tasks = client.get(
        f"/projects/{project_id}/tasks",
        headers=headers,
    )

    assert get_tasks.status_code == 200
    assert len(get_tasks.json()) == 1

    get_task = client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert get_task.status_code == 200

    update_task = client.patch(
        f"/tasks/{task_id}",
        json={"status": "done"},
        headers=headers,
    )

    assert update_task.status_code == 200
    assert update_task.json()['status'] == 'done'

    delete_task = client.delete(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert delete_task.status_code == 204

    delete_task2 = client.delete(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert delete_task2.status_code == 404


def test_task_permissions():
    headers1 = get_auth_headers("test1234@gmail.com")

    create_project = client.post(
        "/projects",
        json={"title": "My First Project", "description": "Testing FastAPI"},
        headers=headers1,
    )

    project_a_id = create_project.json()["id"]

    create_task = client.post(
        f"/projects/{project_a_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers1,
    )

    task_a_id = create_task.json()["id"]

    headers2 = get_auth_headers("test12345@gmail.com")

    create_task1 = client.post(
        f"/projects/{project_a_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers2,
    )

    assert create_task1.status_code == 403

    get_tasks = client.get(
        f"/projects/{project_a_id}/tasks",
        headers=headers2,
    )

    assert get_tasks.status_code == 403

    get_task = client.get(
        f"/tasks/{task_a_id}",
        headers=headers2,
    )

    assert get_task.status_code == 403

    update_task = client.patch(
        f"/tasks/{task_a_id}",
        json={"status": "done"},
        headers=headers2,
    )

    assert update_task.status_code == 403

    delete_task = client.delete(
        f"/tasks/{task_a_id}",
        headers=headers2,
    )

    assert delete_task.status_code == 403


def test_task_not_found():
    headers = get_auth_headers("notfound_user@gmail.com")
    non_existent_id = 999999

    create_task = client.post(
        f"/projects/{non_existent_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers,
    )
    assert create_task.status_code == 404

    get_task = client.get(
        f"/tasks/{non_existent_id}",
        headers=headers,
    )
    assert get_task.status_code == 404