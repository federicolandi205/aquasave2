"""Notificaciones Telegram opcionales configuradas solo mediante variables de entorno."""

import json
import logging
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.models import Measurement, Prototype

logger = logging.getLogger(__name__)


def send_alert(prototype: Prototype, measurement: Measurement) -> bool:
    """Envía aviso MEDIO/ALTO; la falta de configuración o red no pierde la medición."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False
    level = {"AMARILLO": "MEDIO", "ROJO": "ALTO"}.get(measurement.estado_alerta.value, "")
    if not level:
        return False
    text = (
        f"AQUASAVE · ALERTA {level}\n"
        f"Dispositivo: {prototype.nombre} ({prototype.codigo_unico})\n"
        f"Nivel de agua: {measurement.nivel_agua_cm:.1f} cm\n"
        f"Fecha: {measurement.fecha_hora.isoformat()}"
    )
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=4) as response:
            return 200 <= response.status < 300
    except (URLError, TimeoutError, OSError):
        logger.exception("No se pudo enviar el aviso de Telegram")
        return False
