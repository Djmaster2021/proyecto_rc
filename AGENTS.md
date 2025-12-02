# Repository Guidelines

## Project Structure & Module Organization
- Core Django config lives in `proyecto_rc/` (settings, URLs, ASGI/WSGI).
- Feature apps: `accounts/` (auth and allauth), `dentista/` (clinic dashboard), `paciente/` (patient flows), `domain/` (business logic, notifications), `api/` (DRF endpoints).
- Templates in `templates/`; shared components in `templates/_components/`. Static assets in `static/` and per-app under `*/static/`.
- Scripts/utilities: `manage.py`, `docker-compose.yml`, `reset_tablas.py`, `google_oauth_setup.py`.
- Locale resources under `locale/`.

## Build, Test, and Development Commands
- Create env and install deps:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Local DB (MySQL, default port 3307): ensure `MYSQL_DB_*` vars, then `python manage.py migrate`.
- Run dev server: `python manage.py runserver 0.0.0.0:8000`.
- Admin user: `python manage.py createsuperuser`.
- Docker option: `docker-compose up --build` (uses `.env` values for MySQL).
- Collect static for prod: `python manage.py collectstatic --no-input`.
- Tests: `python manage.py test` (Django test runner).

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indent, snake_case for functions/vars, PascalCase for classes. Keep views thin; put business logic in `domain/`.
- Django: prefer class-based views where possible; keep serializers in `api/serializers.py`; URL namespaced per app (`accounts`, `dentista`, `paciente`, `api`).
- Templates: extend `templates/_components/base_site.html` when possible; keep per-app templates under their app directory.
- Static: bundle per app in `app/static/app/` to avoid collisions.

## Testing Guidelines
- Place tests alongside apps (`*/tests.py`). Use descriptive method names: `test_<behavior>`.
- Prefer factory-style object creation over fixtures; mock external services (SMTP, MercadoPago, Google) where relevant.
- Run `python manage.py test appname` during development; aim to cover views, serializers, and permissions.

## Commit & Pull Request Guidelines
- Commits: imperative mood, concise scope (e.g., `Add patient dashboard charts`). Avoid bundling unrelated changes.
- Branching: use feature branches like `feature/<short-desc>` or `fix/<issue-key>`.
- PRs: include purpose, screenshots for UI changes, steps to reproduce/verify, and linked issue/ticket. Note any env vars or migrations.

## Security & Configuration Tips
- Required env vars (examples): `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `MYSQL_DB_*`, `EMAIL_*`, OAuth keys for Google, and any MercadoPago credentials (`paciente/mp_service.py`).
- Never commit secrets; keep `.env` out of version control. Rotate keys before sharing environments.
- For production, set `DEBUG=false`, configure SMTP, and ensure `STATIC_ROOT`/`MEDIA_ROOT` are writable by the server.
