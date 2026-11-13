"""Punto de entrada de la aplicación FastAPI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes import router
from app.auth import router as auth_router

# FastAPI crea automáticamente documentación OpenAPI y Swagger UI.
app = FastAPI(title="AQUASAVE API", version="1.0.0", description="API para sensores de nivel de agua.")
app.include_router(router)
app.include_router(auth_router)
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")


@app.get("/", tags=["Inicio"])
def home():
    """Entrega la plataforma web y mantiene la documentación en /docs."""
    return FileResponse(WEB_DIR / "index.html")
