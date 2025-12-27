# Mapa del proyecto

## Web / Backend (Django)
- `manage.py`: comando principal de Django.
- `proyecto_rc/`: configuración global (settings, urls, wsgi/asgi, middleware).
- `accounts/`: autenticación (login propio + allauth), adaptadores, URLs, templates y estáticos propios.
- `api/`: endpoints DRF (slots, citas, chatbot, health, pagos) y serializers/tests.
- `dentista/`: vistas, URLs, templates y estáticos del dashboard del dentista.
- `paciente/`: vistas, servicios (mp_service), URLs, templates y estáticos para pacientes.
- `domain/`: modelos de negocio, AI helpers, notificaciones, comandos y lógica compartida.
- `templates/`: plantillas compartidas (landing, allauth, componentes, emails).
- `static/`: assets globales (img/js/css/manuales). `staticfiles/` es la salida de collectstatic.

## Mobile (Android)
- `mobile/ConsultorioDentalRC/`: app Android en Kotlin.
  - `app/src/main/java/...`: código (MainActivity, WebViewFragment, API client, etc.).
  - `app/src/main/res/`: layouts, navegación, recursos.
  - `gradle/libs.versions.toml`: versiones de dependencias.
  - `app/build.gradle.kts`: configuración; usa BASE_URL desde `gradleLocalProperties`. Firma con debug si faltan credenciales.

## Operación / DevOps
- `docker-compose.yml`: servicios de base de datos (MySQL, phpMyAdmin).
- `ops/dev_up.sh` / `ops/dev_down.sh`: scripts para levantar/bajar DB + túnel + runserver.
- `ops/run_prod.sh`: arranque gunicorn (ejemplo prod).
- `ops/env.prod.example`: plantilla de variables de entorno prod.
- `ops/runbook_deploy.md`: checklist de despliegue (Cloudflare, Google, health, HTTPS).
- `.github/workflows/`: CI backend (tests) y Android (lint/assembleDebug).

## Datos / Utilidades
- `backups/`: dumps SQL de respaldo.
- `media/`: uploads (perfiles, comprobantes) en entorno local.
- `google_credentials/`: credenciales/token para Google Calendar (opcional, ignorado en git).
- `secrets/`: carpeta ignorada para `.env.private` u otros secretos locales.
- `docs/`: documentación adicional (ej. `chatbot_knowledge.yaml`).
- `requirements.txt`: dependencias Python.
- `README.md`: guía general.

## Scripts varios
- `static.sh`, `templates.sh`: utilidades para desplegar assets/plantillas.
- `reset_tablas.py`: reseteo de datos (uso con cuidado en dev).
- `test_chatbot.sh`: helper para pruebas del chatbot.
