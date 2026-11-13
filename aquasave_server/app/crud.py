"""Consultas y operaciones de escritura en la base de datos."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


def create_prototype(db: Session, data: schemas.PrototypeCreate) -> models.Prototype:
    """Inserta un prototipo y confirma la transacción."""
    item = models.Prototype(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_prototypes(db: Session, skip: int = 0, limit: int = 100) -> list[models.Prototype]:
    """Devuelve prototipos paginados, del más nuevo por identificador."""
    return list(db.scalars(select(models.Prototype).order_by(models.Prototype.id).offset(skip).limit(limit)))


def get_prototype(db: Session, prototype_id: int) -> models.Prototype | None:
    """Busca un prototipo por su clave primaria."""
    return db.get(models.Prototype, prototype_id)


def update_prototype(db: Session, item: models.Prototype, data: schemas.PrototypeUpdate) -> models.Prototype:
    """Aplica únicamente los campos incluidos en el cuerpo de la petición."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_prototype(db: Session, item: models.Prototype) -> None:
    """Elimina un prototipo y, por cascada, sus mediciones."""
    db.delete(item)
    db.commit()


def create_measurement(db: Session, data: schemas.MeasurementCreate) -> models.Measurement:
    """Guarda una medición nueva."""
    item = models.Measurement(**data.model_dump(exclude_none=True))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_measurements(db: Session, skip: int = 0, limit: int = 100) -> list[models.Measurement]:
    """Devuelve mediciones recientes primero y limita el tamaño de la respuesta."""
    query = select(models.Measurement).order_by(models.Measurement.fecha_hora.desc(), models.Measurement.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(query))


def get_measurement(db: Session, measurement_id: int) -> models.Measurement | None:
    """Busca una medición por su clave primaria."""
    return db.get(models.Measurement, measurement_id)


def prototype_history(db: Session, prototype_id: int, skip: int = 0, limit: int = 100) -> list[models.Measurement]:
    """Devuelve el historial reciente de un prototipo en orden descendente."""
    query = (
        select(models.Measurement)
        .where(models.Measurement.prototype_id == prototype_id)
        .order_by(models.Measurement.fecha_hora.desc(), models.Measurement.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(query))
