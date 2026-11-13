# AQUASAVE — Plataforma web, API y PostgreSQL

Este directorio contiene la API y la plataforma web AQUASAVE para registrar prototipos instalados en arroyos y consultar las mediciones que envían. Está hecha con Python 3.13, FastAPI, SQLAlchemy 2, PostgreSQL, Alembic y Uvicorn. La web vive en `web/` y FastAPI la sirve en la misma dirección que la API. El esquema PostgreSQL existente se conserva.

## Qué contiene el proyecto

- `app/database.py`: lee la URL de conexión, crea el motor SQLAlchemy y entrega sesiones a las rutas.
- `app/models.py`: define las tablas `prototypes` y `measurements` y su relación uno a muchos.
- `app/schemas.py`: valida los JSON que entran y define la forma de las respuestas.
- `app/crud.py`: contiene las operaciones de lectura, creación, actualización y borrado.
- `app/routes.py`: conecta esas operaciones con las direcciones HTTP.
- `app/main.py`: crea la aplicación FastAPI.
- `web/index.html` y `web/assets/`: interfaz adaptable; consume la API REST y actualiza datos cada 15 segundos.
- `alembic/`: configuración y migración que crea las tablas.
- `.env`: URL local de la base; cambiala por tus credenciales y no la compartas.
- `requirements.txt`: bibliotecas necesarias.

## Antes de empezar: términos básicos

### 1. ¿Qué es PostgreSQL?

PostgreSQL es un sistema gestor de bases de datos relacionales. Es un programa que mantiene los datos guardados en tablas, controla quién puede leerlos o modificarlos y responde consultas. En AQUASAVE, cada prototipo ocupa una fila en `prototypes` y cada lectura ocupa una fila en `measurements`.

### 2. ¿Qué es SQLAlchemy? ¿Qué hace un ORM?

SQLAlchemy es una biblioteca de Python para conectarse y trabajar con bases de datos SQL. Su parte ORM (mapeador objeto-relacional) permite representar una tabla como una clase de Python: por ejemplo, `Prototype` representa `prototypes`. El ORM traduce operaciones Python a SQL y convierte filas de vuelta a objetos. PostgreSQL sigue siendo quien guarda los datos; el ORM no es una base de datos.

### La relación de las dos tablas

Un prototipo tiene cero o muchas mediciones. Cada medición pertenece a un único prototipo mediante `measurements.prototype_id`, una clave foránea que apunta a `prototypes.id`. Si se elimina un prototipo, también se eliminan sus mediciones asociadas. `codigo_unico` no puede repetirse. La temperatura puede quedar vacía. Las fechas de instalación se envían como `AAAA-MM-DD`; las fechas y horas de medición aceptan ISO 8601 y se completan con la hora del servidor si no se envían.

## Instalación y configuración en Windows

### 3. Instalar PostgreSQL

1. En el sitio oficial de PostgreSQL, abrí **Download** → **Windows** y elegí el instalador de EDB.
2. Ejecutá el instalador descargado. En **Select Components**, dejá seleccionados PostgreSQL Server y pgAdmin 4. Command Line Tools es útil y puede quedar seleccionado. Stack Builder es opcional.
3. En **Data Directory**, conservá la carpeta sugerida salvo que tengas un motivo para cambiarla.
4. En **Password**, definí una contraseña para el usuario administrador `postgres`. Guardala: se pide al conectar pgAdmin. No la pegues en el proyecto ni la confundas con la contraseña del usuario de aplicación.
5. En **Port**, conservá `5432`, salvo que esa dirección ya esté ocupada.
6. Conservá la configuración regional predeterminada y terminá la instalación. Abrí **pgAdmin 4** desde el menú Inicio.

### 4. Crear la base y el usuario en pgAdmin

La contraseña del usuario de aplicación se configura al crear el login role. Estos pasos asumen una instalación local en el puerto `5432`.

**Crear el usuario (rol de inicio de sesión):**

1. En el panel izquierdo de pgAdmin, expandí **Servers**. Si aparece **Register Server**, elegí el servidor PostgreSQL instalado. Ingresá la contraseña de `postgres` que elegiste durante la instalación y, si es tu computadora personal, podés marcar **Save password**.
2. Expandí el servidor y hacé clic derecho en **Login/Group Roles**.
3. Elegí **Create** → **Login/Group Role…**.
4. En la pestaña **General**, escribí `aquasave_user` en **Name**.
5. En **Definition**, escribí una contraseña propia en **Password** y repetila en **Confirm password**. Para los ejemplos, anotá esta clave temporalmente.
6. En **Privileges**, dejá **Can login?** en **Yes**. No marques privilegios de superusuario.
7. Pulsá **Save**.

**Crear la base de datos:**

1. Hacé clic derecho en **Databases** → **Create** → **Database…**.
2. Escribí `aquasave_db` en **Database**.
3. En **Owner**, elegí `aquasave_user`.
4. Pulsá **Save**. Las tablas se crearán después al ejecutar Alembic.

Si no aparece el rol en **Owner**, refrescá **Login/Group Roles**. Si el rol no puede crear las tablas por permisos, como administrador abrí **Tools** → **Query Tool** conectado a `aquasave_db` y ejecutá `GRANT ALL ON SCHEMA public TO aquasave_user;`. En versiones nuevas de PostgreSQL, si todavía falla la creación de objetos en `public`, ejecutá también `GRANT CREATE ON SCHEMA public TO aquasave_user;`.

### 5. Configurar `.env`

En el Explorador de archivos, abrí la carpeta `aquasave_server` y editá `.env` con Bloc de notas o VS Code. Reemplazá `CAMBIAR_ESTA_CLAVE` por la contraseña que asignaste a `aquasave_user`:

```dotenv
DATABASE_URL=postgresql+psycopg://aquasave_user:TU_CLAVE@localhost:5432/aquasave_db
```

No agregues espacios alrededor de `=`. Si tu contraseña contiene caracteres reservados de una URL (por ejemplo `@`, `:`, `/`, `#` o `%`), codificalos como URL; por ejemplo `@` se escribe `%40`. Una alternativa sencilla para el primer entorno local es elegir una contraseña larga que use letras y números. El archivo `.env` está excluido de Git mediante `.gitignore`; no lo publiques.

### 6. Preparar Python e instalar bibliotecas

Abrí **PowerShell**. Podés abrirlo desde Inicio; luego escribí estos comandos, uno por uno. En cada línea, `cd` cambia la carpeta actual:

```powershell
cd "$HOME\Documents\ChatGPT\New project\aquasave_server"
```

`py -3.13 --version` confirma que el lanzador encuentra Python 3.13:

```powershell
py -3.13 --version
```

Creá un entorno virtual aislado para este proyecto y activalo:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación por su política de ejecución, en esa ventana podés activar solo para el proceso actual con `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y luego repetir el comando de activación. Cuando el entorno esté activo, la línea de PowerShell suele mostrar `(.venv)`.

Actualizá pip e instalá las dependencias. `-r` significa “leer la lista desde este archivo”:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`psycopg[binary]` instala el controlador que permite a Python hablar con PostgreSQL sin compilarlo localmente. No hace falta instalar un servidor PostgreSQL mediante pip; eso ya se hizo con el instalador de Windows.

## Crear las tablas con Alembic

### 7. ¿Qué es Alembic y cómo ejecutarlo?

Una migración describe cambios ordenados en la estructura de la base: crear una tabla, agregar una columna, etc. Alembic registra cuáles se aplicaron y permite repetir la puesta en marcha en otra máquina.

La migración inicial `alembic/versions/0001_create_initial_tables.py` ya viene incluida. Desde PowerShell, dentro de `aquasave_server` y con `.venv` activo, ejecutá:

```powershell
alembic upgrade head
```

`upgrade` pide aplicar cambios y `head` significa la revisión más nueva. Alembic lee `DATABASE_URL` desde `.env`, se conecta a `aquasave_db` y crea `prototypes`, `measurements` y `alembic_version`. Si aparece un error de autenticación, revisá la URL y la clave. Si dice que no puede conectar, confirmá que el servidor PostgreSQL está iniciado y que el puerto coincide.

Para revisar las migraciones aplicadas:

```powershell
alembic current
```

Para cambios futuros de modelos: modificá `app/models.py`, generá una propuesta con `alembic revision --autogenerate -m "descripcion del cambio"`, revisá el archivo generado y aplicalo con `alembic upgrade head`. La autogeneración propone cambios, pero siempre hay que inspeccionar la migración antes de aplicarla.

## Iniciar y usar la API

### 8. Iniciar Uvicorn

Desde la misma carpeta y con el entorno virtual activo:

```powershell
python -m uvicorn app.main:app --reload
```

`app.main:app` indica “el objeto `app` del archivo `app/main.py`”. `--reload` reinicia el servidor al editar código y es apropiado para desarrollo local. Dejá esa ventana abierta. Uvicorn muestra una dirección como `http://127.0.0.1:8000`.

### 9. Probar con Swagger desde el navegador

Abrí `http://127.0.0.1:8000/docs`. Swagger UI es una página interactiva generada por FastAPI.

Para probar una operación: desplegá su fila, pulsá **Try it out**, escribí el JSON de ejemplo en **Request body**, luego pulsá **Execute**. La respuesta aparece debajo. Primero creá un prototipo y copiá el `id` que devuelva; después usá ese número como `prototype_id` al crear una medición.

JSON para `POST /prototypes`:

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

JSON para `POST /measurements` (reemplazá `1` por el id devuelto arriba):

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

`fecha_hora` puede omitirse y se completa con el reloj de PostgreSQL. Para consultar, ejecutá **GET /prototypes**, **GET /prototypes/{prototype_id}**, **GET /measurements**, **GET /measurements/{measurement_id}** o **GET /prototype/{prototype_id}/history**. En rutas con `{...}`, pulsá **Try it out** y escribí el identificador. `skip` y `limit` sirven para paginar listas. `PUT /prototypes/{prototype_id}` acepta los campos que quieras modificar; `DELETE /prototypes/{prototype_id}` borra ese prototipo y sus mediciones.

### 10. Comprobar en PostgreSQL que se guardaron los datos

En pgAdmin, expandí **Servers** → tu servidor → **Databases** → `aquasave_db` → **Schemas** → **public** → **Tables**. Si la lista no está actualizada, hacé clic derecho en **Tables** → **Refresh**. Deben aparecer `prototypes`, `measurements` y `alembic_version`.

Para ver las filas, clic derecho en `prototypes` → **View/Edit Data** → **All Rows**. Repetí para `measurements`. También podés abrir **Tools** → **Query Tool** sobre `aquasave_db` y ejecutar:

```sql
SELECT * FROM prototypes ORDER BY id;
SELECT * FROM measurements ORDER BY fecha_hora DESC;
```

Cada `SELECT` muestra las filas persistidas en PostgreSQL. Cerrá el servidor y volvelo a iniciar: los datos seguirán allí porque viven en la base, no en la memoria de FastAPI.

## Endpoints disponibles

| Método | Dirección | Uso |
|---|---|---|
| POST | `/prototypes` | Crear un prototipo |
| GET | `/prototypes` | Listar prototipos (`skip`, `limit`) |
| GET | `/prototypes/{id}` | Obtener un prototipo |
| PUT | `/prototypes/{id}` | Actualizar campos de un prototipo |
| DELETE | `/prototypes/{id}` | Borrar prototipo e historial asociado |
| POST | `/measurements` | Crear una medición |
| GET | `/measurements` | Listar mediciones paginadas; acepta `prototype_id`, `estado_alerta`, `fecha_desde`, `fecha_hasta` |
| GET | `/measurements/{id}` | Obtener una medición |
| GET | `/prototype/{id}/history` | Historial de un prototipo (`skip`, `limit`) |
| GET | `/measurements/latest` | Última medición guardada por prototipo |
| GET | `/alerts` | Mediciones en nivel AMARILLO o ROJO |
| GET | `/statistics?days=7&prototype_id=1` | Agregados y serie histórica para gráficos |

Los errores de validación devuelven `422`, un recurso inexistente `404` y un `codigo_unico` duplicado `409`. Esta versión es una base funcional para desarrollo. Antes de exponerla públicamente, agregá autenticación para dispositivos, HTTPS, reglas de red y una política de retención/respaldos acorde al despliegue.

## Ejecutar la plataforma web

Con la base de datos PostgreSQL configurada y las migraciones aplicadas según los pasos anteriores, inicia Uvicorn desde `aquasave_server`:

```powershell
python -m uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000/` para la plataforma y `http://127.0.0.1:8000/docs` para Swagger. La interfaz consume la API del mismo servidor, no requiere un segundo proceso frontend. Se actualiza cada 15 segundos. Si PostgreSQL no está disponible, se informa en pantalla; no se cargan lecturas de demostración.

Para registrar o modificar prototipos, define `ADMIN_API_KEY` en el entorno del servidor. Las operaciones de los sensores (`POST /measurements`) siguen usando el contrato existente y no requieren esa clave.

## Pruebas automatizadas

Instala las dependencias de desarrollo y ejecuta la suite. Las pruebas usan SQLite en memoria y no escriben sobre PostgreSQL:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests -p no:cacheprovider
python -m coverage run -m pytest tests -p no:cacheprovider
python -m coverage report --include="app/*" --fail-under=60
```

La cobertura configurada en el informe mide el backend Python dentro de `app/`; no instrumenta el frontend JavaScript/CSS ni las migraciones Alembic.

La conexión utiliza los endpoints originales (`/prototypes`, `/measurements`, `/prototype/{id}/history`) además de `/measurements/latest`, `/alerts` y `/statistics`. La vista de alertas deriva eventos de las mediciones AMARILLO/ROJO, por lo que no duplica información en otra tabla. Los niveles se corresponden con VERDE=BAJO, AMARILLO=MEDIO y ROJO=ALTO. Se considera conectado un prototipo activo con lectura de los últimos 5 minutos.

## Configuración y despliegue

### Desplegar en Render con Blueprint

El archivo `../render.yaml` configura un Web Service Python para esta carpeta y una base Render PostgreSQL. Para desplegarlo:

1. Publica en GitHub el commit que contiene `render.yaml` y `aquasave_server/`.
2. En Render, elige **New +** → **Blueprint**, conecta el repositorio `aquasave2` y selecciona la rama `main`.
3. Revisa los recursos detectados y pulsa **Apply**. Render instalará `requirements.txt`, ejecutará `alembic upgrade head` y arrancará Uvicorn enlazado al puerto `$PORT`.
4. Al terminar, abre la URL `onrender.com` del servicio. `/health` comprueba la conexión de la API con PostgreSQL; `/docs` abre Swagger.
5. Si usarás Telegram, añade `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` en **Environment** del servicio. No pongas esos secretos en GitHub.

El Blueprint genera automáticamente `ADMIN_API_KEY` y `AUTH_SECRET_KEY`; cópialos desde el panel de Render cuando debas usarlos. La base gratuita de Render vence a los 30 días; antes de esa fecha, actualízala a un plan persistente o exporta y migra los datos. Los servicios web gratuitos se suspenden tras 15 minutos sin tráfico y tardan en reactivarse cuando reciben una nueva petición. Esta configuración gratuita sirve para probar y presentar el proyecto; para conservar el historial de forma continua, usa una base con persistencia. Revisa los límites y el costo actual antes de elegir un plan.

- Mantén `DATABASE_URL` y las credenciales fuera del frontend. `.env` es local y está ignorado por Git. Configura `ADMIN_API_KEY` con una clave secreta larga; el alta, edición y baja de prototipos requieren `X-Admin-Key`. La interfaz solicita la clave al guardar y la conserva solo en la sesión del navegador.
- Para activar notificaciones configura `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` como variables de entorno del servidor. Si no están definidas, las lecturas siguen guardándose y la web muestra alertas derivadas; el token nunca se envía al navegador. Los fallos de Telegram se registran en el log del backend y no descartan la medición.
- El proyecto actual usa PostgreSQL, no SQLite. Es una base relacional existente; no se crea una segunda base. En un proveedor cloud configura `DATABASE_URL` como variable secreta y usa PostgreSQL gestionado con persistencia y respaldos. El filesystem efímero de algunos planes gratuitos no es adecuado para guardar una SQLite de producción.
- Configura el servicio cloud para instalar `requirements.txt` y arrancar con `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` (ajusta la expansión de `$PORT` a la plataforma). Aplica `alembic upgrade head` como comando de despliegue antes de iniciar. La disponibilidad de planes gratuitos cambia por proveedor; verifica límites y retención antes de desplegar.

## Alcance actual de la interfaz

Incluye resumen, monitoreo de última lectura, mapa Leaflet con filtros, historial paginado y exportación CSV completa, gráficos Chart.js, alta y edición protegidas de prototipos, alertas derivadas e información del proyecto. El historial API limita cada respuesta a 500 filas; la vista de historial navega en páginas de 20 y aplica los filtros en el servidor. El dashboard conserva datos reales de la base y presenta estados vacíos cuando aún no hay mediciones.


## Usuarios y autenticación OAuth2

La API ofrece el flujo OAuth2 `password` con tokens Bearer. Para una instalación local, copiá `AUTH_SECRET_KEY` y `ADMIN_API_KEY` a `.env` y reemplazá los ejemplos por secretos aleatorios largos (mínimo 32 caracteres para `AUTH_SECRET_KEY`). Instalá las nuevas dependencias con `python -m pip install -r requirements.txt` y aplicá la migración con `python -m alembic upgrade head`.

La administración de cuentas usa la misma cabecera `X-Admin-Key` del servidor:

- `POST /users`: crear cuenta (`email`, `nombre`, `password`; mínimo 8 caracteres).
- `GET /users`: listar cuentas.
- `PUT /users/{id}`: cambiar email, nombre o contraseña.
- `DELETE /users/{id}`: baja lógica; pone `activo=false` y registra `eliminado_en`, sin borrar la fila. La cuenta ya no puede autenticarse.
- `POST /auth/token`: canjear formulario OAuth2 (`username` = email, `password`) por un token Bearer válido por 12 horas.
- `GET /auth/me`: consultar la cuenta autenticada con `Authorization: Bearer <access_token>`.

La creación de cuentas es administrativa; no hay registro público. Swagger UI en `/docs` permite probar el endpoint de token. Las contraseñas se guardan con PBKDF2-HMAC-SHA256 y nunca se devuelven en las respuestas.
