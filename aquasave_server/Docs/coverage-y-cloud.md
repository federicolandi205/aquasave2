# Cobertura de pruebas y opciones cloud

## Cobertura

Se ejecutó la suite ampliada con Coverage.py, incluyendo el backend `app/*`:

```text
Name                       Stmts   Miss  Cover
----------------------------------------------
app\__init__.py                0      0   100%
app\auth.py                  129      5    96%
app\crud.py                   36      2    94%
app\database.py               16      5    69%
app\main.py                   14      0   100%
app\models.py                 46      0   100%
app\routes.py                108      4    96%
app\schemas.py                57      0   100%
app\services\__init__.py       0      0   100%
app\services\telegram.py      23      0   100%
TOTAL                        429     16    96%
```

**Resultado:** 14 pruebas pasaron y el backend Python instrumentado alcanza **96%**: 413 de 429 líneas ejecutables cubiertas, por encima del objetivo de 70%. Las pruebas cubren autenticación y errores, CRUD/rutas, filtros y paginación, integridad referencial y éxito/fallo de Telegram.

**Alcance:** `--include="app/*"` limita el dato a módulos Python bajo `app`. No mide `web/assets/app.js`, CSS/HTML, migraciones Alembic ni los propios tests; por lo tanto 96% describe el backend Python, no todos los lenguajes/archivos del proyecto. Para reproducir desde la raíz, con dependencias instaladas:

```powershell
python -m coverage run -m pytest tests -p no:cacheprovider
python -m coverage report --include="app/*"
```

`-p no:cacheprovider` evita recolectar directorios temporales `pytest-cache-files-*` presentes en este checkout.

## Proveedor cloud y nivel gratuito

En los archivos de este checkout no hay proveedor cloud elegido ni configuración específica de Render, AWS, Azure, GCP u otro. El README propone de forma genérica desplegar Uvicorn y usar PostgreSQL gestionado; advierte que los límites gratuitos cambian y que el filesystem efímero no sirve para persistir SQLite en producción. Por eso la conclusión basada en el repositorio es: **no se puede afirmar que el proyecto actualmente tenga un proveedor cloud con free tier configurado**.

La presencia o disponibilidad actual de planes gratuitos requiere verificación externa en la fecha de despliegue y no queda demostrada por el código. La aplicación necesita un servicio Python para la API y PostgreSQL persistente con respaldos. Antes de escoger proveedor, confirmar cuotas, suspensión por inactividad, límites de base y retención de datos. No guardar secretos ni depender de almacenamiento efímero para datos de producción.
