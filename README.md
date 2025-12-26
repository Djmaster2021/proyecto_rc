# 🦷 Sistema de Gestión Dental RC (WEB Y MOVIL).

![Estado](https://img.shields.io/badge/Estado-Finalizado-success) ![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Django](https://img.shields.io/badge/Django-5.0-green) ![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)

Plataforma integral para el Consultorio Dental **Rodolfo Castellón**: agenda, pagos, recordatorios, chatbot y sincronización con Google Calendar.

## Características
- Panel del dentista con agenda diaria/semana/mes, reportes y gestión de pacientes.
- Flujos del paciente: agendar/reprogramar/cancelar, pagar penalizaciones, completar perfil.
- Recordatorios y confirmaciones por correo, con enlaces de confirmación seguros.
- Integración Google Calendar (OAuth) y pagos con MercadoPago.
- Interfaz responsiva con modo oscuro/claro y chatbot embebido.

## Requisitos
- Python 3.11+, pip, virtualenv.
- MySQL 8 (puedes levantarlo con Docker).
- Credenciales SMTP (Gmail con contraseña de aplicación).
- Opcional: Google OAuth (calendar) y credenciales de MercadoPago.

## Configuración rápida (local)
1) Crear entorno: `python -m venv .venv && source .venv/bin/activate`  
2) Instalar dependencias: `pip install -r requirements.txt`  
3) Copiar variables: `cp .env.example .env` y completar valores (secret key, DB, SMTP, Google/MercadoPago).  
4) Base de datos: inicia MySQL (puedes usar `docker compose up db -d`), luego `python manage.py migrate`.  
5) Usuario admin: `python manage.py createsuperuser`.  
6) Servidor: `python manage.py runserver 0.0.0.0:8000` y entra a `http://127.0.0.1:8000`.

## Variables de entorno (referencia)
- `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.
- `MYSQL_DB_NAME`, `MYSQL_DB_USER`, `MYSQL_DB_PASSWORD`, `MYSQL_DB_HOST`, `MYSQL_DB_PORT`, `MYSQL_ROOT_PASSWORD` (para Docker).
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `DJANGO_SEND_EMAILS` (en dev viene desactivado por defecto), `SUPPORT_EMAIL`.
- `MERCADOPAGO_PUBLIC_KEY`, `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_TEST_PAYER_EMAIL` (email del comprador de prueba cuando uses token TEST-), `MERCADOPAGO_WEBHOOK_SECRET`.
- `MERCADOPAGO_FAKE_SUCCESS`: si `1/true`, en sandbox marca el pago como completado sin ir a MercadoPago (útil para desarrollar cuando el checkout de prueba falla).
- `GOOGLE_CALENDAR_ID` y archivos en `google_credentials/credentials.json` + `token.json`.
- OAuth Google (allauth): `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` (usa cliente tipo “Aplicación web”).
- Chatbot IA (opcional Gemini): `GEMINI_API_KEY` (si está presente se enciende automáticamente), `CHATBOT_IA_ENABLED` (`auto/true/false`), `GEMINI_MODEL_NAME`, `CHATBOT_MAX_CONTEXT`.

### Integración Google Calendar (opcional, desactivada)
- La app funciona sin credenciales ni sincronización. Si no quieres usar Calendar, no necesitas crear `google_credentials/`.
- Para activarlo: crea la carpeta `google_credentials/`, coloca `credentials.json` y ejecuta `python google_oauth_setup.py` (requiere instalar `google-auth`, `google-auth-oauthlib`, `google-api-python-client`).
- Ajusta `GOOGLE_CALENDAR_ID` en `.env` al calendario donde se escribirán eventos.

## Docker (solo base de datos)
- Levanta MySQL y phpMyAdmin: `docker compose up db phpmyadmin -d`.  
  - MySQL expone `3307` en tu host; ajusta `MYSQL_DB_PORT=3307` en `.env` si corres Django fuera del contenedor.
- La app Django se ejecuta en tu máquina con `runserver` (no hay servicio web en el compose).

## Tareas útiles
- Recordatorios diarios: `python manage.py enviar_recordatorios` (usa SMTP y links de confirmación).  
- Correo de prueba SMTP: `python manage.py enviar_correo_prueba --to tu_correo@example.com` (respeta `SEND_EMAILS`; usa `--force` para ignorarlo).  
- Generar token OAuth de Google: `python google_oauth_setup.py` tras colocar `google_credentials/credentials.json`.  
- Colección de estáticos para producción: `python manage.py collectstatic --no-input`.  
- Reiniciar datos locales (desarrollo): `python reset_tablas.py` (pide confirmación; usa `--force` si sabes lo que haces).
- Healthcheck: `GET /api/health/` (sin auth) devuelve host/SITE_BASE_URL y estado.
- Crear dentista por defecto (si la BD está vacía): `python manage.py seed_default_dentist` (usa envs `DEFAULT_DENTISTA_*` opcionales).
- Webhook MercadoPago (prod): configura la URL pública a `/paciente/pagos/webhook/`.
- Cron sugerido para recordatorios (ejemplo): `0 * * * * cd /home/diego/Escritorio/proyecto_rc/proyecto_rc && .venv/bin/python manage.py enviar_recordatorios_citas >> /var/log/rc_recordatorios.log 2>&1` (plantilla en `ops/cron_recordatorios.example`).
- Flags de seguridad configurables en `.env`: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SECURE_PROXY_SSL_HEADER`, `DRF_THROTTLE_ANON`, `DRF_THROTTLE_USER`.

## Estructura rápida
- `proyecto_rc/` configuración Django.  
- Apps: `accounts/`, `dentista/`, `paciente/`, `domain/` (modelos/negocio), `api/` (DRF).  
- Plantillas compartidas en `templates/` y estáticos globales en `static/`; cada app tiene sus propios assets.

## Tests
- Ejecuta `python manage.py test` (recomendable usar una base separada o SQLite en local para no tocar datos reales).
- CI: GitHub Actions (`.github/workflows/ci.yml`) ejecuta los tests de Django (accounts, api).

## Arranque rápido con túnel
- `bash ops/dev_up.sh`: levanta `docker compose up -d db`, inicia `cloudflared tunnel run consultoriorc` si está instalado y ejecuta `runserver` en `0.0.0.0:8001`.
- `bash ops/dev_down.sh`: detiene `cloudflared` (si lo inició dev_up) y el contenedor `db`.

## Producción
- `DEBUG=False`, configure `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`.
- Revisa permisos de escritura en `MEDIA_ROOT` y `STATIC_ROOT`, y activa HTTPS en el servidor frontal (Nginx/Apache).
- Usa `ops/env.prod.example` como plantilla para tu `.env` de producción y arranca con `bash ops/run_prod.sh` (gunicorn en 0.0.0.0:8000). Coloca un proxy reverso (Nginx) al frente.
