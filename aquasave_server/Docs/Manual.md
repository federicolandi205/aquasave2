# Manual de instalación y uso de AQUASAVE

Guía del checkout `aquasave_server` para desarrollo local en Windows. Se basa en `README.md` y archivos fuente del repositorio.

## Requisitos

- Windows, Python 3.13 y PowerShell.
- PostgreSQL instalado y en ejecución (puerto por defecto 5432), o una instancia PostgreSQL accesible.
- Git opcional si el repositorio aún no está descargado.

## 1. Preparar la base de datos

En pgAdmin crear un login role, por ejemplo `aquasave_user`, con contraseña propia y sin privilegio de superusuario. Crear la base `aquasave_db` asignándole ese usuario como owner. Si el rol no puede crear objetos, otorgar permisos de creación sobre el esquema `public`.

## 2. Configurar Python y secretos

Desde PowerShell, entrar a la carpeta del proyecto y ejecutar:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Copiar `.env.example` a `.env`; completar `DATABASE_URL` con el usuario, contraseña, host, puerto y base correctos. También definir claves aleatorias largas para `ADMIN_API_KEY` y `AUTH_SECRET_KEY` (mínimo 32 caracteres para esta última). Para mensajes Telegram, completar opcionalmente `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`. `.env` está ignorado por Git y debe mantenerse privado. Si la contraseña contiene caracteres reservados de URL, codificarlos.

Ejemplo de URL local:

```dotenv
DATABASE_URL=postgresql+psycopg://aquasave_user:TU_CLAVE@localhost:5432/aquasave_db
```

## 3. Aplicar las migraciones

Con entorno virtual activo, desde la raíz `aquasave_server`:

```powershell
python -m alembic upgrade head
python -m alembic current
```

Las migraciones crean `prototypes`, `measurements`, `users` y `alembic_version`. Consultar [database-schemas.md](database-schemas.md) antes de operar sobre el esquema.

## 4. Iniciar la aplicación

```powershell
python -m uvicorn app.main:app --reload
```

Abrir `http://127.0.0.1:8000/` para la plataforma y `http://127.0.0.1:8000/docs` para Swagger. Dejar abierta la terminal mientras se usa el servicio. `--reload` es para desarrollo.

## 5. Uso básico

La API gestiona prototipos y lecturas. Para crear/editar/borrar prototipos se requiere `X-Admin-Key` con el valor de `ADMIN_API_KEY`; la interfaz lo solicita al guardar. Las lecturas de sensores se ingresan con `POST /measurements`. En Swagger, desplegar endpoint, seleccionar **Try it out**, completar JSON y **Execute**.

Ejemplo para registrar un prototipo (requiere clave administrativa):

```json
{
  "nombre": "Sensor Puente Centro",
  "codigo_unico": "AQUA-001",
  "latitud": -34.6037,
  "longitud": -58.3816,
  "barrio": "Centro",
  "ciudad": "Buenos Aires",
  "fecha_instalacion": "2026-09-27",
  "estado": "activo"
}
```

Ejemplo de lectura, sustituyendo `prototype_id` por el id recibido:

```json
{
  "prototype_id": 1,
  "distancia_cm": 42.5,
  "nivel_agua_cm": 57.5,
  "porcentaje": 57.5,
  "estado_alerta": "VERDE",
  "temperatura": 18.2
}
```

La web actualiza el resumen cada 15 segundos, permite ver mapa/historial/analítica/alertas y exportar mediciones CSV. Para OAuth2, primero un administrador crea una cuenta en `POST /users`; después el cliente solicita token a `POST /auth/token` y usa `Authorization: Bearer ...`. Ver [autenticacion-oauth2.md](autenticacion-oauth2.md). Los avisos de Telegram son opcionales y se envían solo para niveles AMARILLO/ROJO; ver [telegram-bot.md](telegram-bot.md).

## Endpoints principales

| Método | Ruta | Uso |
|---|---|---|
| GET/POST | `/prototypes` | Listar/crear prototipos |
| GET/PUT/DELETE | `/prototypes/{id}` | Consultar, editar o eliminar prototipo |
| GET/POST | `/measurements` | Listar/registrar lecturas |
| GET | `/measurements/{id}` | Consultar lectura |
| GET | `/prototype/{id}/history` | Historial del dispositivo |
| GET | `/measurements/latest`, `/alerts`, `/statistics` | Últimas lecturas, alertas derivadas y agregados |
| POST/GET | `/auth/token`, `/auth/me` | Autenticación OAuth2 e identidad |
| POST/GET/PUT/DELETE | `/users[/{id}]` | Gestión administrativa de cuentas |

## Operación y solución de problemas

- Error de conexión DB: verificar PostgreSQL encendido, host/puerto/base y `DATABASE_URL`.
- Error de permisos al migrar: revisar que el rol sea owner o tenga permisos en `public`.
- Error de clave administrativa: revisar que el header coincida con `ADMIN_API_KEY` y reiniciar tras cambiar `.env`.
- Error al emitir token: `AUTH_SECRET_KEY` debe tener al menos 32 caracteres; la cuenta debe existir y estar activa.
- UI sin datos: verificar estado de API y que haya prototipos/mediciones; no hay datos demo.
- Telegram no avisa: comprobar token, chat id, permiso de conversación, nivel AMARILLO/ROJO y logs del backend.

## Cambios de esquema y despliegue

Modificar modelos, generar una revisión con `python -m alembic revision --autogenerate -m "descripcion"`, revisar a mano el archivo y aplicar con `python -m alembic upgrade head`. En despliegue usar secretos como variables del entorno, HTTPS, base PostgreSQL persistente, respaldos y el comando Uvicorn adecuado al proveedor. No usar `--reload` en producción.
