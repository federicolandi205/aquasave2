"""Pruebas de contratos y operaciones principales de la API."""


def create_prototype(client, payload, headers):
    response = client.post("/prototypes", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_static_dashboard_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "AQUASAVE" in response.text


def test_admin_key_required_for_prototype_changes(client, prototype_payload):
    response = client.post("/prototypes", json=prototype_payload)
    assert response.status_code == 401


def test_duplicate_prototype_code_is_rejected(client, prototype_payload, admin_headers):
    create_prototype(client, prototype_payload, admin_headers)
    response = client.post("/prototypes", json=prototype_payload, headers=admin_headers)
    assert response.status_code == 409


def test_measurements_latest_alerts_and_statistics(client, prototype_payload, admin_headers):
    prototype = create_prototype(client, prototype_payload, admin_headers)
    for level, water in (("VERDE", 15.0), ("AMARILLO", 45.0), ("ROJO", 75.0)):
        response = client.post("/measurements", json={
            "prototype_id": prototype["id"],
            "distancia_cm": 100 - water,
            "nivel_agua_cm": water,
            "porcentaje": water,
            "estado_alerta": level,
        })
        assert response.status_code == 201

    latest = client.get("/measurements/latest")
    assert latest.status_code == 200
    assert len(latest.json()) == 1
    assert latest.json()[0]["estado_alerta"] == "ROJO"

    alerts = client.get("/alerts")
    assert alerts.status_code == 200
    assert [row["estado_alerta"] for row in alerts.json()] == ["ROJO", "AMARILLO"]

    stats = client.get("/statistics?days=7")
    assert stats.status_code == 200
    assert stats.json()["total_mediciones"] == 3
    assert stats.json()["alertas"] == 2


def test_measurement_filters_and_device_history(client, prototype_payload, admin_headers):
    prototype = create_prototype(client, prototype_payload, admin_headers)
    client.post("/measurements", json={
        "prototype_id": prototype["id"], "distancia_cm": 70,
        "nivel_agua_cm": 30, "porcentaje": 30, "estado_alerta": "VERDE",
    })
    filtered = client.get(f"/measurements?prototype_id={prototype['id']}&estado_alerta=VERDE")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    history = client.get(f"/prototype/{prototype['id']}/history")
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_invalid_coordinates_are_rejected(client, prototype_payload, admin_headers):
    prototype_payload["latitud"] = 100
    response = client.post("/prototypes", json=prototype_payload, headers=admin_headers)
    assert response.status_code == 422
