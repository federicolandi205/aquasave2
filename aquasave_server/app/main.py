"""Punto de entrada de la aplicación FastAPI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.routes import router
from app.auth import router as auth_router
from app.database import engine

# FastAPI crea automáticamente documentación OpenAPI y Swagger UI.
app = FastAPI(title="AQUASAVE API", version="1.0.0", description="API para sensores de nivel de agua.")
app.include_router(router)
app.include_router(auth_router)
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")


@app.get("/health", include_in_schema=False)
def health_check():
    """Render usa esta ruta para comprobar que la API y PostgreSQL responden."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "database": "ok"}


@app.get("/", tags=["Inicio"])
def home():
    """Entrega la plataforma web y mantiene la documentación en /docs."""
    return FileResponse(WEB_DIR / "index.html")
