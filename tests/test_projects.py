# 2. Тест: Создание и чтение своего проекта
async def test_create_and_get_project(client, auth_headers):
    headers = await auth_headers("owner@gmail.com")

    # Создаём проект
    create_res = await client.post(
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
    get_res = await client.get(f"/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "My First Project"


# 3. Тест на безопасность (Ownership): Чужой юзер не имеет доступа к проекту
async def test_user_cannot_access_other_user_project(client, auth_headers):
    # Создаём первого пользователя и его проект
    user1_headers = await auth_headers("user1@gmail.com")
    create_res = await client.post(
        "/projects",
        json={"title": "Secret Project of User 1", "description": "Top secret"},
        headers=user1_headers,
    )
    user1_project_id = create_res.json()["id"]

    # Создаём ВТОРОГО пользователя и получаем ЕГО токен
    user2_headers = await auth_headers("user2@gmail.com")

    # Второй юзер пытается прочитать проект первого юзера
    response = await client.get(f"/projects/{user1_project_id}", headers=user2_headers)

    # Проверяем, что сработала наша проверка на 403 Forbidden
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Not enough permissions"


# 4. Тест: Удаление проекта и проверка 404
async def test_delete_project_success(client, auth_headers):
    headers = await auth_headers("deleter@gmail.com")

    # Создаём проект
    create_res = await client.post(
        "/projects",
        json={"title": "To be deleted", "description": "Bye"},
        headers=headers,
    )
    project_id = create_res.json()["id"]

    # Удаляем (ожидаем 204 No Content)
    delete_res = await client.delete(f"/projects/{project_id}", headers=headers)
    assert delete_res.status_code == 204

    # Пробуем запросить удалённый проект снова — ожидаем 404
    get_res = await client.get(f"/projects/{project_id}", headers=headers)
    assert get_res.status_code == 404
    assert get_res.json()["error"]["message"] == "Project not found"
