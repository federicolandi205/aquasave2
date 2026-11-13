# Esquema de base de datos de AQUASAVE

Este documento describe el esquema que el código y las migraciones del repositorio definen. PostgreSQL es el motor previsto; SQLAlchemy mapea las tablas y Alembic aplica cambios versionados. La conexión se toma de `DATABASE_URL` (`app/database.py`); no se guarda la contraseña en el código.

## Diagrama

```text
prototypes (1) ──────────── (N) measurements
     id PK                         prototype_id FK → prototypes.id
                                   ON DELETE CASCADE

users (independiente; autenticación OAuth2)
```

## Tablas

### `prototypes`

| Columna | Tipo / regla | Comentario |
|---|---|---|
| `id` | integer, PK, índice | Identificador del dispositivo. |
| `nombre` | varchar(120), no nulo | Nombre visible. |
| `codigo_unico` | varchar(64), único, indexado, no nulo | Identificador de negocio; los duplicados se rechazan. |
| `latitud` | float, no nulo, −90 a 90 | Coordenada validada también por `ck_prototypes_latitud`. |
| `longitud` | float, no nulo, −180 a 180 | Coordenada validada también por `ck_prototypes_longitud`. |
| `barrio`, `ciudad` | varchar(120), no nulo | Ubicación descriptiva. |
| `fecha_instalacion` | date, no nulo | Fecha de instalación. |
| `estado` | enum `activo` / `inactivo`, no nulo, default `activo` | Disponibilidad administrativa del prototipo. |

### `measurements`

| Columna | Tipo / regla | Comentario |
|---|---|---|
| `id` | integer, PK, índice | Identificador de lectura. |
| `prototype_id` | integer, FK indexada, no nulo | Refiere a `prototypes.id`; borrado en cascada. |
| `distancia_cm` | float, no nulo, ≥ 0 | Distancia medida. |
| `nivel_agua_cm` | float, no nulo, ≥ 0 | Nivel de agua calculado/recibido. |
| `porcentaje` | float, no nulo, 0–100 | Porcentaje normalizado. |
| `estado_alerta` | enum `VERDE` / `AMARILLO` / `ROJO`, no nulo | La web los presenta como BAJO / MEDIO / ALTO. |
| `temperatura` | float, nullable | Lectura opcional. |
| `fecha_hora` | timestamp con zona, no nulo, default `now()` | Hora de la base si el cliente no la envía. |

La relación ORM usa `cascade="all, delete-orphan"`; eliminar un prototipo elimina su historial. Las alertas no tienen tabla propia: `/alerts` deriva filas AMARILLO/ROJO de `measurements`.

### `users`

Agregada en revisión `0002_add_users`, independiente de los sensores.

| Columna | Tipo / regla | Comentario |
|---|---|---|
| `id` | integer, PK, índice | Identificador de cuenta. |
| `email` | varchar(254), único, indexado, no nulo | Se normaliza a minúsculas en la API. |
| `nombre` | varchar(120), no nulo | Nombre de la cuenta. |
| `password_hash` | varchar(256), no nulo | Hash PBKDF2-HMAC-SHA256; nunca se devuelve en las respuestas. |
| `activo` | boolean, no nulo, default true | Cuenta desactivada no puede autenticarse. |
| `eliminado_en` | timestamp con zona, nullable | Se usa para la baja lógica; la fila permanece. |

## Código y migraciones relacionados

- `app/models.py`: modelos ORM, enums, restricciones y relación.
- `app/database.py`: motor, sesiones y `get_db()`.
- `app/crud.py`: operaciones de persistencia para prototipos/mediciones.
- `app/schemas.py`: validación y contratos JSON de la API.
- `alembic/versions/0001_create_initial_tables.py`: crea `prototypes`, `measurements`, enums, índices y claves.
- `alembic/versions/0002_add_users.py`: crea usuarios e índice único de email.
- `alembic/env.py`, `alembic.ini`: configuración de Alembic.

Para aplicar el esquema localmente, configurar `DATABASE_URL` y ejecutar `python -m alembic upgrade head`. Las migraciones son la fuente operativa para crear/actualizar las tablas; inspeccionar siempre una migración autogenerada antes de desplegarla.
