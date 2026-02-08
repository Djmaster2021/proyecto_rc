# Sistema de Gestion Dental RC

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![CI](https://github.com/Djmaster2021/proyecto_rc/actions/workflows/ci.yml/badge.svg)

Plataforma web para operacion integral de consultorio dental: agenda clinica, gestion de pacientes, pagos, recordatorios y automatizaciones de soporte.

## Espanol

### Resumen Ejecutivo
Sistema orientado a flujo real de consultorio, con panel para dentista, portal para paciente e integraciones opcionales de pagos y calendario.

### Capacidades Principales
- Agenda diaria, semanal y mensual para el dentista.
- Gestion de pacientes, historial y reportes operativos.
- Flujos del paciente: agendar, reprogramar, cancelar, pago de penalizaciones y perfil.
- Recordatorios y confirmaciones por correo con enlaces seguros.
- Integraciones opcionales: Google Calendar (OAuth), MercadoPago y chatbot IA.

### Stack Tecnologico
- Backend: Django 5 + Django REST Framework
- Frontend: Django Templates + JS modular
- Base de datos: MySQL 8 (Docker) o equivalente
- Mobile complementario: Android (modulo en `mobile/ConsultorioDentalRC`)
- CI: GitHub Actions para pruebas backend y build Android

### Inicio Rapido (Local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d db
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Acceso local:
- App: `http://127.0.0.1:8000`
- Admin: `http://127.0.0.1:8000/admin`
- phpMyAdmin (opcional): `http://127.0.0.1:8081`

### Variables de Entorno Relevantes
- Core Django: `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`
- Base de datos: `MYSQL_DB_NAME`, `MYSQL_DB_USER`, `MYSQL_DB_PASSWORD`, `MYSQL_DB_HOST`, `MYSQL_DB_PORT`, `MYSQL_ROOT_PASSWORD`
- Correo: `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `DJANGO_SEND_EMAILS`, `SUPPORT_EMAIL`
- Pagos: `MERCADOPAGO_PUBLIC_KEY`, `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET`, `MERCADOPAGO_FAKE_SUCCESS`
- Calendar: `GOOGLE_CALENDAR_ID`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- Chatbot IA: `CHATBOT_IA_ENABLED`, `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `CHATBOT_MAX_CONTEXT`

Referencia completa: `.env.example`

### Comandos Operativos
```bash
python manage.py test
python manage.py enviar_recordatorios
python manage.py enviar_correo_prueba --to tu_correo@example.com
python manage.py seed_default_dentist
python manage.py collectstatic --no-input
```

Healthcheck:
- `GET /api/health/`

### Produccion
- Usa `ops/env.prod.example` como plantilla de entorno.
- Ejecuta `bash ops/run_prod.sh` para levantar Gunicorn.
- Coloca Nginx/Apache como proxy reverso con HTTPS.
- Revisa `ops/runbook_deploy.md` para checklist operativo.

## English

### Executive Summary
Web platform for dental clinic operations, including scheduling, patient management, payments, reminders, and optional integrations.

### Key Capabilities
- Dentist dashboard with day/week/month scheduling views.
- Patient workflows for booking, rescheduling, canceling, and penalty payments.
- Email reminders and confirmations with secure links.
- Optional integrations: Google Calendar (OAuth), MercadoPago, and AI chatbot.

### Technology
- Backend: Django 5 + Django REST Framework
- Frontend: Django templates + modular JavaScript
- Database: MySQL 8 (Docker setup available)
- Mobile companion: Android module in `mobile/ConsultorioDentalRC`
- CI: GitHub Actions for backend tests and Android build

### Local Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d db
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Project Structure
- `proyecto_rc/`: Django settings and entry points
- `accounts/`: authentication and account flows
- `dentista/`: dentist panel and operations
- `paciente/`: patient portal and patient-side flows
- `domain/`: core domain models and business rules
- `api/`: REST API endpoints and serializers
- `ops/`: deployment and operations scripts
- `docs/`: technical documentation

## Notes
- This repository contains both web and Android code.
- For full tree reference, see `docs/structure.md`.
- Author: Diego Adrian Aceves Magana
