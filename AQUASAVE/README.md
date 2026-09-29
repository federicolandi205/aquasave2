# AQUASAVE — API, PostgreSQL y migraciones

Este directorio contiene una API de desarrollo para registrar prototipos instalados en arroyos y las mediciones que envían. Está hecha con Python 3.13, FastAPI, SQLAlchemy 2, PostgreSQL, Alembic y Uvicorn. Los archivos Python incluyen comentarios junto a las partes importantes para que puedas seguir el flujo.

## Qué contiene el proyecto

- `app/database.py`: lee la URL de conexión, crea el motor SQLAlchemy y entrega sesiones a las rutas.
- `app/models.py`: define las tablas `prototypes` y `measurements` y su relación uno a muchos.
- `app/schemas.py`: valida los JSON que entran y define la forma de las respuestas.
- `app/crud.py`: contiene las operaciones de lectura, creación, actualización y borrado.
- `app/routes.py`: conecta esas operaciones con las direcciones HTTP.
- `app/main.py`: crea la aplicación FastAPI.
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
| GET | `/measurements` | Listar mediciones (`skip`, `limit`) |
| GET | `/measurements/{id}` | Obtener una medición |
| GET | `/prototype/{id}/history` | Historial de un prototipo (`skip`, `limit`) |

Los errores de validación devuelven `422`, un recurso inexistente `404` y un `codigo_unico` duplicado `409`. Esta versión es una base funcional para desarrollo. Antes de exponerla públicamente, agregá autenticación para dispositivos, HTTPS, reglas de red y una política de retención/respaldos acorde al despliegue.
