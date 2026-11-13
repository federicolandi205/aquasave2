"""Rutas HTTP de la API de AQUASAVE."""

from datetime import date, datetime, timedelta, timezone
import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.database import get_db
from app.services.telegram import send_alert

router = APIRouter()


def require_admin(x_admin_key: str | None = Header(default=None)):
    """Protege cambios administrativos con una clave configurada en el servidor."""
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Falta configurar ADMIN_API_KEY en el servidor.")
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Clave administrativa inválida.")


def _measurement_dict(row):
    measurement, prototype = row
    return {
        "id": measurement.id, "prototype_id": measurement.prototype_id,
        "nombre": prototype.nombre, "codigo_unico": prototype.codigo_unico,
        "nivel_agua_cm": measurement.nivel_agua_cm, "porcentaje": measurement.porcentaje,
        "estado_alerta": measurement.estado_alerta.value,
        "fecha_hora": measurement.fecha_hora.isoformat(),
    }


@router.get("/measurements/latest")
def read_latest_measurements(db: Session = Depends(get_db)):
    """Última lectura guardada por prototipo, para el panel de monitoreo."""
    ranked = select(
        models.Measurement.id.label("measurement_id"),
        func.row_number().over(
            partition_by=models.Measurement.prototype_id,
            order_by=(models.Measurement.fecha_hora.desc(), models.Measurement.id.desc()),
        ).label("position"),
    ).subquery()
    rows = db.execute(
        select(models.Measurement, models.Prototype)
        .join(ranked, ranked.c.measurement_id == models.Measurement.id)
        .join(models.Prototype)
        .where(ranked.c.position == 1)
    ).all()
    return [_measurement_dict(row) for row in rows]


@router.get("/alerts")
def read_alerts(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    """Las alertas se derivan de mediciones, sin duplicar una tabla de eventos."""
    rows = db.execute(
        select(models.Measurement, models.Prototype).join(models.Prototype)
        .where(models.Measurement.estado_alerta.in_([models.EstadoAlerta.AMARILLO, models.EstadoAlerta.ROJO]))
        .order_by(models.Measurement.fecha_hora.desc(), models.Measurement.id.desc()).limit(limit)
    ).all()
    return [{**_measurement_dict(row), "estado": "registrada"} for row in rows]


@router.get("/statistics")
def read_statistics(
    days: int = Query(default=7, ge=1, le=365),
    prototype_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    """Agregados históricos calculados sobre las mediciones existentes."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(models.Measurement).where(models.Measurement.fecha_hora >= cutoff)
    if prototype_id is not None:
        query = query.where(models.Measurement.prototype_id == prototype_id)
    measurements = list(db.scalars(query.order_by(models.Measurement.fecha_hora)).all())
    counts = {level.value: 0 for level in models.EstadoAlerta}
    for item in measurements:
        counts[item.estado_alerta.value] += 1
    return {
        "periodo_dias": days,
        "total_mediciones": len(measurements),
        "por_nivel": counts,
        "alertas": counts["AMARILLO"] + counts["ROJO"],
        "serie": [{"fecha_hora": m.fecha_hora.isoformat(), "prototype_id": m.prototype_id,
                   "nivel_agua_cm": m.nivel_agua_cm, "porcentaje": m.porcentaje,
                   "estado_alerta": m.estado_alerta.value} for m in measurements],
        "por_prototipo": [
            {"prototype_id": prototype_id, "mediciones": count}
            for prototype_id, count in db.execute(
                select(models.Measurement.prototype_id, func.count(models.Measurement.id))
                .where(models.Measurement.fecha_hora >= cutoff)
                .group_by(models.Measurement.prototype_id)
            ).all()
        ],
    }


@router.post("/prototypes", response_model=schemas.PrototypeRead, status_code=status.HTTP_201_CREATED)
def create_prototype(data: schemas.PrototypeCreate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Registra un dispositivo; el código único no puede repetirse."""
    try:
        return crud.create_prototype(db, data)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="El codigo_unico ya existe.") from exc


@router.get("/prototypes", response_model=list[schemas.PrototypeRead])
def read_prototypes(
    skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista prototipos; skip y limit permiten recorrer resultados grandes."""
    return crud.list_prototypes(db, skip, limit)


@router.get("/prototypes/{prototype_id}", response_model=schemas.PrototypeRead)
def read_prototype(prototype_id: int, db: Session = Depends(get_db)):
    """Devuelve un prototipo o el error HTTP 404."""
    item = crud.get_prototype(db, prototype_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Prototipo no encontrado.")
    return item


@router.put("/prototypes/{prototype_id}", response_model=schemas.PrototypeRead)
def edit_prototype(prototype_id: int, data: schemas.PrototypeUpdate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Actualiza los campos enviados del prototipo existente."""
    item = crud.get_prototype(db, prototype_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Prototipo no encontrado.")
    try:
        return crud.update_prototype(db, item, data)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="El codigo_unico ya existe.") from exc


@router.delete("/prototypes/{prototype_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_prototype(prototype_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Elimina el prototipo y las lecturas asociadas."""
    item = crud.get_prototype(db, prototype_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Prototipo no encontrado.")
    crud.delete_prototype(db, item)
    return None


@router.post("/measurements", response_model=schemas.MeasurementRead, status_code=status.HTTP_201_CREATED)
def create_measurement(data: schemas.MeasurementCreate, db: Session = Depends(get_db)):
    """Registra una lectura del sensor; prototype_id debe existir."""
    try:
        item = crud.create_measurement(db, data)
        if item.estado_alerta in (models.EstadoAlerta.AMARILLO, models.EstadoAlerta.ROJO):
            prototype = crud.get_prototype(db, item.prototype_id)
            if prototype:
                send_alert(prototype, item)
        return item
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail="El prototype_id no existe o los datos no son válidos.") from exc


@router.get("/measurements", response_model=list[schemas.MeasurementRead])
def read_measurements(
    skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500),
    prototype_id: int | None = Query(default=None, gt=0),
    estado_alerta: models.EstadoAlerta | None = None,
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Lista mediciones recientes con filtros opcionales y paginación."""
    query = select(models.Measurement).order_by(models.Measurement.fecha_hora.desc(), models.Measurement.id.desc())
    if prototype_id is not None:
        query = query.where(models.Measurement.prototype_id == prototype_id)
    if estado_alerta is not None:
        query = query.where(models.Measurement.estado_alerta == estado_alerta)
    if fecha_desde is not None:
        query = query.where(models.Measurement.fecha_hora >= datetime.combine(fecha_desde, datetime.min.time(), tzinfo=timezone.utc))
    if fecha_hasta is not None:
        query = query.where(models.Measurement.fecha_hora < datetime.combine(fecha_hasta + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
    return list(db.scalars(query.offset(skip).limit(limit)).all())


@router.get("/measurements/{measurement_id}", response_model=schemas.MeasurementRead)
def read_measurement(measurement_id: int, db: Session = Depends(get_db)):
    """Devuelve una medición o HTTP 404 si no existe."""
    item = crud.get_measurement(db, measurement_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Medición no encontrada.")
    return item


@router.get("/prototype/{prototype_id}/history", response_model=list[schemas.MeasurementRead])
def read_prototype_history(
    prototype_id: int,
    skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Muestra el historial de lecturas de un prototipo existente."""
    if crud.get_prototype(db, prototype_id) is None:
        raise HTTPException(status_code=404, detail="Prototipo no encontrado.")
    return crud.prototype_history(db, prototype_id, skip, limit)
