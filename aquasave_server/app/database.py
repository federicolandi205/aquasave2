"""Configuración de la conexión y componentes compartidos de SQLAlchemy."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Lee las variables definidas en .env desde el directorio del proyecto.
load_dotenv()

# La URL completa se mantiene fuera del código para poder cambiar credenciales.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta configurar la variable DATABASE_URL.")

# Render Postgres entrega postgresql://; usamos el driver psycopg 3 que ya
# forma parte de requirements.txt (sin exigir psycopg2).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL.removeprefix("postgres://")
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL.removeprefix("postgresql://")

# El motor administra las conexiones entre la aplicación y PostgreSQL.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Cada petición obtendrá su propia sesión de base de datos.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM."""


def get_db():
    """Entrega una sesión a FastAPI y la cierra incluso si ocurre un error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
