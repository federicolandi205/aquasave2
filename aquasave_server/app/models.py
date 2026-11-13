"""Modelos ORM: las clases representan las tablas de PostgreSQL."""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import CheckConstraint, Date, DateTime, Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EstadoPrototipo(str, Enum):
    """Estados permitidos para un dispositivo instalado."""

    ACTIVO = "activo"
    INACTIVO = "inactivo"


class EstadoAlerta(str, Enum):
    """Niveles de alerta calculados por el dispositivo o el sistema."""

    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"


class Prototype(Base):
    """Un prototipo/sensor instalado en una ubicación."""

    __tablename__ = "prototypes"
    __table_args__ = (
        CheckConstraint("latitud >= -90 AND latitud <= 90", name="ck_prototypes_latitud"),
        CheckConstraint("longitud >= -180 AND longitud <= 180", name="ck_prototypes_longitud"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo_unico: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)
    barrio: Mapped[str] = mapped_column(String(120), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(120), nullable=False)
    fecha_instalacion: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoPrototipo] = mapped_column(
        SAEnum(EstadoPrototipo, name="estado_prototipo", values_callable=lambda enum: [item.value for item in enum]),
        default=EstadoPrototipo.ACTIVO,
        nullable=False,
    )

    # Un prototipo tiene muchas mediciones; borrar el prototipo borra su historial.
    measurements: Mapped[list["Measurement"]] = relationship(
        back_populates="prototype", cascade="all, delete-orphan"
    )


class Measurement(Base):
    """Una lectura enviada por un sensor."""

    __tablename__ = "measurements"
    __table_args__ = (
        CheckConstraint("distancia_cm >= 0", name="ck_measurements_distancia"),
        CheckConstraint("nivel_agua_cm >= 0", name="ck_measurements_nivel"),
        CheckConstraint("porcentaje >= 0 AND porcentaje <= 100", name="ck_measurements_porcentaje"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prototype_id: Mapped[int] = mapped_column(
        ForeignKey("prototypes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    distancia_cm: Mapped[float] = mapped_column(Float, nullable=False)
    nivel_agua_cm: Mapped[float] = mapped_column(Float, nullable=False)
    porcentaje: Mapped[float] = mapped_column(Float, nullable=False)
    estado_alerta: Mapped[EstadoAlerta] = mapped_column(
        SAEnum(EstadoAlerta, name="estado_alerta", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
    )
    temperatura: Mapped[float | None] = mapped_column(Float, nullable=True)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Cada medición pertenece a un solo prototipo.
    prototype: Mapped[Prototype] = relationship(back_populates="measurements")


class User(Base):
    """Cuenta de acceso; la baja se registra sin borrar la fila."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    eliminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
