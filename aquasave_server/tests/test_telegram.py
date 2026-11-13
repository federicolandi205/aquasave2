"""Pruebas aisladas del emisor de avisos de Telegram."""

from types import SimpleNamespace
from datetime import datetime, timezone

from app.services import telegram


def item(level):
    return SimpleNamespace(estado_alerta=SimpleNamespace(value=level), nivel_agua_cm=72.5,
                           fecha_hora=datetime(2026, 11, 9, 12, tzinfo=timezone.utc))


def prototype():
    return SimpleNamespace(nombre="Sensor Río", codigo_unico="AQUA-7")


def test_telegram_skips_without_config_or_for_green(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert telegram.send_alert(prototype(), item("ROJO")) is False
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    assert telegram.send_alert(prototype(), item("VERDE")) is False


def test_telegram_sends_alert_and_handles_network_errors(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "secret-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    captured = {}

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *_): return None

    def successful(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = request.data.decode()
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(telegram, "urlopen", successful)
    assert telegram.send_alert(prototype(), item("AMARILLO")) is True
    assert "secret-token" in captured["url"]
    assert "ALERTA MEDIO" in captured["body"]
    assert captured["timeout"] == 4

    def failed(*_, **__):
        raise TimeoutError("timeout")

    monkeypatch.setattr(telegram, "urlopen", failed)
    assert telegram.send_alert(prototype(), item("ROJO")) is False
