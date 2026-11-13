# Avisos de Telegram

## Qué hace el proyecto

El código disponible implementa un emisor de notificaciones, no un bot conversacional con comandos entrantes. `app/services/telegram.py` llama al método `sendMessage` de Telegram Bot API cuando una medición nueva está en nivel `AMARILLO` o `ROJO`. El mensaje incluye nivel, dispositivo/código, nivel del agua y hora. Las alertas de la web, en cambio, se consultan desde las mediciones guardadas.

## Configuración

1. Crear un bot en Telegram con BotFather y obtener el token.
2. Obtener el `chat_id` de destino (la conversación debe haber iniciado/permitido recibir mensajes del bot).
3. Definir en el entorno privado del servidor `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`. `.env.example` muestra los nombres; no poner el token en HTML/JavaScript ni subirlo al repositorio.
4. Reiniciar el backend para cargar las variables.
5. Enviar una medición AMARILLO/ROJO a `POST /measurements` y confirmar recepción y logs del servicio.

## Comportamiento y fallos

`app/routes.py` guarda la medición y luego llama `send_alert`. Si faltan variables o el estado es VERDE, no hace petición. La solicitud usa HTTPS, timeout de cuatro segundos y registra excepciones de red; un fallo de Telegram no revierte ni descarta la lectura. La función devuelve `True` para respuesta HTTP exitosa y `False` en los demás casos.

El README también enumera endpoints de API para datos y gestión, pero no hay en los archivos inspeccionados un worker, webhook, polling, comandos Telegram, registro de usuarios de Telegram ni reintentos persistentes.
