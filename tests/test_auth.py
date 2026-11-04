async def test_register_user_success(client):
    response = await client.post(
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


async def test_register_duplicate_email(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "bob1@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 201

    response = await client.post(
        "/auth/register",
        json={
            "email": "bob1@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Email already registered"


async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={
            "email": "bob2@gmail.com",
            "password": "bobby123",
        },
    )

    response = await client.post(
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


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={
            "email": "bob_wrong_pw@gmail.com",
            "password": "bobby123",
        },
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": "bob_wrong_pw@gmail.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_login_nonexistent_user(client):
    response = await client.post(
        "/auth/login",
        data={
            "username": "nonexistent@gmail.com",
            "password": "bobby123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_get_current_user_success(client):
    await client.post(
        "/auth/register",
        json={
            "email": "bob_wrong_pws@gmail.com",
            "password": "bobby123",
        },
    )

    login_res = await client.post(
        "/auth/login",
        data={
            "username": "bob_wrong_pws@gmail.com",
            "password": "bobby123",
        },
    )
    token = login_res.json()["access_token"]

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "bob_wrong_pws@gmail.com"


async def test_get_current_user_no_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_get_current_user_invalid_token(client):
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalidtoken123"}
    )
    assert response.status_code == 401


async def test_rate_limiter_blocks_after_threshold(client):
    for _ in range(5):
        res = await client.post(
            "/auth/login",
            data={"username": "wrong@test.com", "password": "wrongpassword"},
        )
        assert res.status_code in (400, 401)

    blocked_res = await client.post(
        "/auth/login",
        data={"username": "wrong@test.com", "password": "wrongpassword"},
    )
    assert blocked_res.status_code == 429
    assert blocked_res.json()["detail"] == "Too many requests. Please try again later."
    assert "Retry-After" in blocked_res.headers
