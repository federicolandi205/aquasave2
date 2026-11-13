"""Esquemas Pydantic: validan entradas y definen las respuestas HTTP."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EstadoPrototipoSchema(str, Enum):
    """Valores válidos para el estado del prototipo en la API."""

    ACTIVO = "activo"
    INACTIVO = "inactivo"


class EstadoAlertaSchema(str, Enum):
    """Valores válidos para el estado de alerta en la API."""

    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"


class PrototypeCreate(BaseModel):
    """Campos obligatorios/aceptados al crear un prototipo."""

    nombre: str = Field(min_length=1, max_length=120)
    codigo_unico: str = Field(min_length=1, max_length=64)
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    barrio: str = Field(min_length=1, max_length=120)
    ciudad: str = Field(min_length=1, max_length=120)
    fecha_instalacion: date
    estado: EstadoPrototipoSchema = EstadoPrototipoSchema.ACTIVO


class PrototypeUpdate(BaseModel):
    """Permite modificar parcialmente un prototipo mediante PUT."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    codigo_unico: str | None = Field(default=None, min_length=1, max_length=64)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    barrio: str | None = Field(default=None, min_length=1, max_length=120)
    ciudad: str | None = Field(default=None, min_length=1, max_length=120)
    fecha_instalacion: date | None = None
    estado: EstadoPrototipoSchema | None = None


class PrototypeRead(BaseModel):
    """Forma pública de un prototipo, incluyendo su identificador."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    codigo_unico: str
    latitud: float
    longitud: float
    barrio: str
    ciudad: str
    fecha_instalacion: date
    estado: EstadoPrototipoSchema


class MeasurementCreate(BaseModel):
    """Campos enviados para guardar una nueva lectura."""

    prototype_id: int = Field(gt=0)
    distancia_cm: float = Field(ge=0)
    nivel_agua_cm: float = Field(ge=0)
    porcentaje: float = Field(ge=0, le=100)
    estado_alerta: EstadoAlertaSchema
    temperatura: float | None = None
    fecha_hora: datetime | None = None


class MeasurementRead(BaseModel):
    """Forma pública de una medición guardada."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prototype_id: int
    distancia_cm: float
    nivel_agua_cm: float
    porcentaje: float
    estado_alerta: EstadoAlertaSchema
    temperatura: float | None
    fecha_hora: datetime
