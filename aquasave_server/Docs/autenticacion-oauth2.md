# Autenticación OAuth2 de AQUASAVE

## Alcance implementado

La API implementa OAuth2 con flujo de contraseña y tokens Bearer en `app/auth.py`, montado desde `app/main.py`. En este repositorio “OAuth2” se refiere al intercambio local email/contraseña por un token de acceso; no hay proveedor externo, inicio de sesión social ni integración de OpenAI. La autenticación de administración mediante `X-Admin-Key` es un mecanismo separado.

## Flujo de acceso

1. Una persona administradora crea cuentas mediante `POST /users` con `X-Admin-Key`. No existe registro público.
2. El cliente envía formulario `application/x-www-form-urlencoded` a `POST /auth/token`, usando `username` para el email y `password` para la clave.
3. Si las credenciales son válidas y la cuenta está activa, recibe `access_token`, `token_type: bearer` y `expires_in: 43200` (12 horas).
4. El cliente envía `Authorization: Bearer <access_token>` a rutas protegidas por `current_user`, por ejemplo `GET /auth/me`.

La interfaz web incluida no realiza un flujo de login OAuth2 propio: para altas/ediciones de prototipos solicita `ADMIN_API_KEY` y la conserva en `sessionStorage` durante esa sesión.

## Protección de credenciales y token

- Las contraseñas deben tener 8–128 caracteres y se almacenan con PBKDF2-HMAC-SHA256, salt aleatorio de 16 bytes y 310 000 iteraciones. La comparación usa tiempo constante.
- El token es un JWT compacto firmado con HMAC-SHA256; contiene `sub` (id de usuario) y `exp`. Su firma usa `AUTH_SECRET_KEY` y la expiración se verifica en cada autenticación.
- `AUTH_SECRET_KEY` debe estar definida y tener al menos 32 caracteres. Si no cumple, el servicio responde 503 al crear/verificar tokens.
- `ADMIN_API_KEY` protege `POST/GET/PUT/DELETE /users`; también protege altas, edición y baja de prototipos mediante el router general.
- `DELETE /users/{id}` es baja lógica: fija `activo=false` y `eliminado_en`, y los tokens de cuentas desactivadas dejan de ser válidos.
- En las respuestas de usuario se excluyen `password_hash`.

## Endpoints de usuarios

| Método y ruta | Uso | Control |
|---|---|---|
| `POST /users` | Crear cuenta (`email`, `nombre`, `password`) | `X-Admin-Key`; 409 si email repetido |
| `GET /users` | Listar cuentas | `X-Admin-Key` |
| `PUT /users/{id}` | Actualizar email, nombre o contraseña | `X-Admin-Key` |
| `DELETE /users/{id}` | Desactivar cuenta | `X-Admin-Key` |
| `POST /auth/token` | Obtener token OAuth2 | Credenciales de cuenta |
| `GET /auth/me` | Consultar identidad de token | Bearer válido |

## Configuración y uso local

Copiar `.env.example` a `.env`, generar secretos aleatorios propios y mantenerlos fuera de Git. Definir `AUTH_SECRET_KEY` y `ADMIN_API_KEY`, instalar `requirements.txt` (incluye `python-multipart` para el formulario OAuth2) y aplicar `python -m alembic upgrade head`. Luego iniciar la API y probar `/docs`.

Ejemplo de formulario de token en Swagger: `username=persona@example.com`, `password=...`. En llamadas siguientes usar el botón **Authorize** de Swagger o la cabecera Bearer. No enviar secretos al frontend ni registrar contraseñas/tokens en logs.

## Limitaciones observadas

El código usa un token firmado propio y no una biblioteca JWT/OAuth especializada; el flujo password es para clientes de confianza y no implementa refresh tokens, revocación individual, MFA, scopes/roles ni autorización por recurso. No se observan límites de intentos de login ni política de rotación de claves. Antes de exponer a Internet, servir exclusivamente sobre HTTPS y evaluar un proveedor/servidor de identidad y controles de producción apropiados.
