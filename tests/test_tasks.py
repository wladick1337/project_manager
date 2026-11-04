async def test_task_lifecycle(client, auth_headers):
    headers = await auth_headers("test123@gmail.com")

    create_project = await client.post(
        "/projects",
        json={"title": "My First Project", "description": "Testing FastAPI"},
        headers=headers,
    )

    assert create_project.status_code == 201
    project_id = create_project.json()["id"]

    create_task = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers,
    )

    assert create_task.status_code == 201
    task_data = create_task.json()
    assert task_data["title"] == "My First Task"
    assert "id" in task_data

    task_id = task_data["id"]

    get_tasks = await client.get(
        f"/projects/{project_id}/tasks",
        headers=headers,
    )

    assert get_tasks.status_code == 200
    tasks_data = get_tasks.json()
    assert tasks_data["total"] == 1
    assert len(tasks_data["items"]) == 1

    get_task = await client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert get_task.status_code == 200

    update_task = await client.patch(
        f"/tasks/{task_id}",
        json={"status": "done"},
        headers=headers,
    )

    assert update_task.status_code == 200
    assert update_task.json()["status"] == "done"

    delete_task = await client.delete(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert delete_task.status_code == 204

    delete_task2 = await client.delete(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert delete_task2.status_code == 404


async def test_task_permissions(client, auth_headers):
    headers1 = await auth_headers("test1234@gmail.com")

    create_project = await client.post(
        "/projects",
        json={"title": "My First Project", "description": "Testing FastAPI"},
        headers=headers1,
    )

    project_a_id = create_project.json()["id"]

    create_task = await client.post(
        f"/projects/{project_a_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers1,
    )

    task_a_id = create_task.json()["id"]

    headers2 = await auth_headers("test12345@gmail.com")

    create_task1 = await client.post(
        f"/projects/{project_a_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers2,
    )

    assert create_task1.status_code == 403

    get_tasks = await client.get(
        f"/projects/{project_a_id}/tasks",
        headers=headers2,
    )

    assert get_tasks.status_code == 403

    get_task = await client.get(
        f"/tasks/{task_a_id}",
        headers=headers2,
    )

    assert get_task.status_code == 403

    update_task = await client.patch(
        f"/tasks/{task_a_id}",
        json={"status": "done"},
        headers=headers2,
    )

    assert update_task.status_code == 403

    delete_task = await client.delete(
        f"/tasks/{task_a_id}",
        headers=headers2,
    )

    assert delete_task.status_code == 403


async def test_task_not_found(client, auth_headers):
    headers = await auth_headers("notfound_user@gmail.com")
    non_existent_id = 999999

    create_task = await client.post(
        f"/projects/{non_existent_id}/tasks",
        json={"title": "My First Task", "description": "Testing FastAPI"},
        headers=headers,
    )
    assert create_task.status_code == 404

    get_task = await client.get(
        f"/tasks/{non_existent_id}",
        headers=headers,
    )
    assert get_task.status_code == 404


async def test_task_pagination_and_filtering(client, auth_headers):
    headers = await auth_headers("filter_user@gmail.com")

    # 1. Создаем проект
    proj = await client.post(
        "/projects", json={"title": "Filters Project"}, headers=headers
    )
    proj1 = proj.json()
    proj_id = proj1["id"]

    # 2. Создаем 3 задачи с описанием
    await client.post(
        f"/projects/{proj_id}/tasks",
        json={"title": "Task 1", "description": "Desc 1", "status": "todo"},
        headers=headers,
    )
    await client.post(
        f"/projects/{proj_id}/tasks",
        json={"title": "Task 2", "description": "Desc 2", "status": "todo"},
        headers=headers,
    )
    await client.post(
        f"/projects/{proj_id}/tasks",
        json={"title": "Task 3", "description": "Desc 3", "status": "in_progress"},
        headers=headers,
    )

    # 3. Проверяем фильтрацию по статусу
    res_todo = await client.get(
        f"/projects/{proj_id}/tasks?status=todo", headers=headers
    )
    assert res_todo.status_code == 200
    data_todo = res_todo.json()
    assert data_todo["total"] == 2
    assert len(data_todo["items"]) == 2

    # 4. Проверяем page и size (пагинацию)
    res_page1 = await client.get(
        f"/projects/{proj_id}/tasks?page=1&size=2", headers=headers
    )
    assert res_page1.status_code == 200
    data_page1 = res_page1.json()
    assert data_page1["total"] == 3
    assert data_page1["page"] == 1
    assert data_page1["pages"] == 2
    assert len(data_page1["items"]) == 2
    assert data_page1["items"][0]["title"] == "Task 1"

    res_page2 = await client.get(
        f"/projects/{proj_id}/tasks?page=2&size=2", headers=headers
    )
    assert res_page2.status_code == 200
    data_page2 = res_page2.json()
    assert data_page2["page"] == 2
    assert len(data_page2["items"]) == 1
    assert data_page2["items"][0]["title"] == "Task 3"
