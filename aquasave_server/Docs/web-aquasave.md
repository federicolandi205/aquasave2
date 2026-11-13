# Web AQUASAVE

## Estructura y ejecución

La aplicación web es una interfaz estática servida por FastAPI en la misma dirección que la API. `app/main.py` sirve `web/index.html` en `/` y monta `web/assets` en `/assets`; no se requiere un proceso de frontend aparte ni un paso de compilación según los archivos disponibles.

- `web/index.html`: estructura semántica, navegación y paneles.
- `web/assets/styles.css`: diseño adaptable y estilos.
- `web/assets/app.js`: navegación, consulta de API, gráficos, mapa, filtros y exportación.
- Bibliotecas cargadas desde CDN: Leaflet para mapa y Chart.js para gráficos; también hay fuentes externas.

Con PostgreSQL configurado y migraciones aplicadas, ejecutar `python -m uvicorn app.main:app --reload` y abrir `http://127.0.0.1:8000/`. La API OpenAPI está en `/docs`.

## Funcionalidad que aparece en el código

- Resumen de prototipos, conectividad (lectura en últimos cinco minutos), última medición y alertas.
- Actualización de datos cada 15 segundos, con estado de conexión y mensajes de error cuando falla la API.
- Monitoreo, mapa de sensores, historial paginado, analítica, gestión de dispositivos y alertas.
- Mapa Leaflet con coordenadas, estado y filtros; gráficos Chart.js con niveles y series históricas.
- Exportación CSV de mediciones y formulario de alta/edición de prototipos.
- Lecturas obtenidas de PostgreSQL vía API; no se insertan valores de demostración en la interfaz.

## Consumo de API

El helper `api()` de `web/assets/app.js` usa `fetch`, agrega JSON y transforma errores HTTP en mensajes. Al refrescar, consulta en paralelo:

```javascript
const [devices, latest, stats, alerts] = await Promise.all([
  api('/prototypes?limit=500'),
  api('/measurements/latest'),
  api(`/statistics?days=${state.period}`),
  api('/alerts?limit=500')
]);
```

El código evita insertar cadenas sin escapar en HTML mediante `esc()` en nombres/valores dinámicos. Para cambios administrativos, pide `ADMIN_API_KEY` y envía `X-Admin-Key`; la clave queda en `sessionStorage` de esa pestaña. El token de Telegram y la URL de base nunca se incluyen en el cliente. El frontend actual no incorpora pantalla de inicio de sesión OAuth2.

## Notas de despliegue

FastAPI entrega la web y API desde el mismo origen, lo cual evita configurar CORS para esta interfaz. Se requieren las variables de entorno del backend y un servicio web capaz de ejecutar Uvicorn. La persistencia depende de PostgreSQL externo/gestionado; no guardar base de producción en un filesystem efímero. La interfaz depende de los CDNs de Leaflet, Chart.js, mapas CARTO/OpenStreetMap y Google Fonts; una política CSP y disponibilidad offline requieren trabajo adicional.
