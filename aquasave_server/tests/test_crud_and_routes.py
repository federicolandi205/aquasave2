"""Cobertura de operaciones CRUD y casos de borde de la API."""


def test_prototype_crud_measurement_and_cascade(client, prototype_payload, admin_headers):
    created = client.post("/prototypes", json=prototype_payload, headers=admin_headers)
    assert created.status_code == 201
    prototype_id = created.json()["id"]
    assert client.get("/prototypes?skip=0&limit=1").json()[0]["id"] == prototype_id
    assert client.get(f"/prototypes/{prototype_id}").status_code == 200
    assert client.get("/prototypes/999").status_code == 404

    changed = client.put(f"/prototypes/{prototype_id}", headers=admin_headers,
                         json={"nombre": "Nombre cambiado"})
    assert changed.status_code == 200
    assert changed.json()["nombre"] == "Nombre cambiado"
    assert client.put("/prototypes/999", headers=admin_headers,
                      json={"nombre": "No existe"}).status_code == 404
    assert client.delete("/prototypes/999", headers=admin_headers).status_code == 404

    reading = client.post("/measurements", json={
        "prototype_id": prototype_id, "distancia_cm": 45,
        "nivel_agua_cm": 55, "porcentaje": 55, "estado_alerta": "AMARILLO",
    })
    assert reading.status_code == 201
    measurement_id = reading.json()["id"]
    assert client.get(f"/measurements/{measurement_id}").status_code == 200
    assert client.get("/measurements/999").status_code == 404
    assert len(client.get(f"/prototype/{prototype_id}/history?skip=0&limit=1").json()) == 1
    assert client.get("/prototype/999/history").status_code == 404

    assert client.delete(f"/prototypes/{prototype_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/measurements/{measurement_id}").status_code == 404


def test_measurement_filters_dates_pagination_and_invalid_prototype(client, prototype_payload, admin_headers):
    prototype = client.post("/prototypes", json=prototype_payload, headers=admin_headers).json()
    payload = {"prototype_id": prototype["id"], "distancia_cm": 10, "nivel_agua_cm": 90,
               "porcentaje": 90, "estado_alerta": "ROJO", "fecha_hora": "2026-11-09T12:00:00Z"}
    assert client.post("/measurements", json={**payload, "prototype_id": 987}).status_code == 404
    assert client.post("/measurements", json=payload).status_code == 201
    assert len(client.get("/measurements?fecha_desde=2026-11-09&fecha_hasta=2026-11-09").json()) == 1
    assert client.get("/measurements?fecha_desde=2026-11-10").json() == []
    assert client.get("/measurements?prototype_id=987").json() == []
    assert client.get("/measurements?skip=1").json() == []


def test_admin_key_configuration_and_statistics_validation(client, prototype_payload, admin_headers, monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY")
    assert client.post("/prototypes", json=prototype_payload).status_code == 503
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    assert client.get("/statistics?days=0").status_code == 422
    assert client.get("/alerts?limit=501").status_code == 422
