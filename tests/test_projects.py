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


# 2. Тест: Создание и чтение своего проекта
def test_create_and_get_project():
    headers = get_auth_headers("owner@gmail.com")

    # Создаём проект
    create_res = client.post(
        "/projects",
        json={"title": "My First Project", "description": "Testing FastAPI"},
        headers=headers,
    )
    assert create_res.status_code == 201
    project_data = create_res.json()
    assert project_data["title"] == "My First Project"
    assert "id" in project_data

    project_id = project_data["id"]

    # Запрашиваем созданный проект по id
    get_res = client.get(f"/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "My First Project"


# 3. Тест на безопасность (Ownership): Чужой юзер не имеет доступа к проекту
def test_user_cannot_access_other_user_project():
    # Создаём первого пользователя и его проект
    user1_headers = get_auth_headers("user1@gmail.com")
    create_res = client.post(
        "/projects",
        json={"title": "Secret Project of User 1", "description": "Top secret"},
        headers=user1_headers,
    )
    user1_project_id = create_res.json()["id"]

    # Создаём ВТОРОГО пользователя и получаем ЕГО токен
    user2_headers = get_auth_headers("user2@gmail.com")

    # Второй юзер пытается прочитать проект первого юзера
    response = client.get(f"/projects/{user1_project_id}", headers=user2_headers)

    # Проверяем, что сработала наша проверка на 403 Forbidden
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


# 4. Тест: Удаление проекта и проверка 404
def test_delete_project_success():
    headers = get_auth_headers("deleter@gmail.com")

    # Создаём проект
    create_res = client.post(
        "/projects",
        json={"title": "To be deleted", "description": "Bye"},
        headers=headers,
    )
    project_id = create_res.json()["id"]

    # Удаляем (ожидаем 204 No Content)
    delete_res = client.delete(f"/projects/{project_id}", headers=headers)
    assert delete_res.status_code == 204

    # Пробуем запросить удалённый проект снова — ожидаем 404
    get_res = client.get(f"/projects/{project_id}", headers=headers)
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "Project not found"