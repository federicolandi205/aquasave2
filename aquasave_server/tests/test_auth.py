"""Pruebas del ciclo de vida de cuentas y los tokens OAuth2."""


def create_user(client, admin_headers, email="operador@example.com"):
    response = client.post("/users", headers=admin_headers, json={
        "email": email, "nombre": "Operador", "password": "clave-segura-123",
    })
    return response


def token_for(client, email="operador@example.com", password="clave-segura-123"):
    return client.post("/auth/token", data={"username": email, "password": password})


def test_user_admin_lifecycle_and_oauth_token(client, admin_headers):
    created = create_user(client, admin_headers, "OPERADOR@example.com")
    assert created.status_code == 201
    account = created.json()
    assert account["email"] == "operador@example.com"
    assert "password_hash" not in account
    assert client.get("/users").status_code == 401
    assert len(client.get("/users", headers=admin_headers).json()) == 1

    login = token_for(client)
    assert login.status_code == 200
    assert login.json()["expires_in"] == 43200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/auth/me", headers=headers).json()["id"] == account["id"]

    changed = client.put(f"/users/{account['id']}", headers=admin_headers,
                         json={"nombre": "Operadora", "password": "otra-clave-123"})
    assert changed.status_code == 200
    assert token_for(client).status_code == 401
    assert token_for(client, password="otra-clave-123").status_code == 200

    deactivated = client.delete(f"/users/{account['id']}", headers=admin_headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["activo"] is False
    assert token_for(client, password="otra-clave-123").status_code == 401


def test_auth_rejects_bad_credentials_tokens_and_unconfigured_secret(client, admin_headers, monkeypatch):
    create_user(client, admin_headers)
    assert token_for(client, password="incorrecta").status_code == 401
    good_token = token_for(client).json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": "Bearer invalido"}).status_code == 401
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {good_token[:-1]}x"}).status_code == 401

    monkeypatch.setenv("AUTH_SECRET_KEY", "corta")
    assert client.post("/auth/token", data={"username": "operador@example.com",
                                             "password": "clave-segura-123"}).status_code == 503


def test_user_admin_conflicts_and_missing_records(client, admin_headers):
    account = create_user(client, admin_headers).json()
    assert create_user(client, admin_headers).status_code == 409
    other = create_user(client, admin_headers, "otro@example.com").json()
    assert client.put(f"/users/{other['id']}", headers=admin_headers,
                      json={"email": account["email"]}).status_code == 409
    assert client.put("/users/999", headers=admin_headers, json={"nombre": "Nadie"}).status_code == 404
    assert client.delete("/users/999", headers=admin_headers).status_code == 404
    assert client.post("/users", json={"email": "x@example.com", "nombre": "x",
                                       "password": "12345678"}).status_code == 401
