"""Fixtures de API aisladas de la base real de AQUASAVE."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # SQLite no activa las claves foráneas por defecto; alinearlo con PostgreSQL.
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-auth-secret-key-long-enough-123456")
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def prototype_payload():
    return {
        "nombre": "Sensor de prueba",
        "codigo_unico": "TEST-001",
        "latitud": -34.6,
        "longitud": -58.4,
        "barrio": "Centro",
        "ciudad": "Buenos Aires",
        "fecha_instalacion": "2026-11-09",
        "estado": "activo",
    }


@pytest.fixture()
def admin_headers():
    return {"X-Admin-Key": "test-admin-key"}
