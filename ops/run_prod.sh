#!/usr/bin/env bash
set -euo pipefail

# Arranca la app con gunicorn en modo producción.
# Usa el archivo .env existente (parte de ops/env.prod.example).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  echo "No se encontró .env en ${ROOT_DIR}. Copia ops/env.prod.example a .env y ajusta valores." >&2
  exit 1
fi

GUNICORN_BIN=".venv/bin/gunicorn"
if [[ ! -x "$GUNICORN_BIN" ]]; then
  if command -v gunicorn >/dev/null 2>&1; then
    GUNICORN_BIN="$(command -v gunicorn)"
    echo "Usando gunicorn del sistema: $GUNICORN_BIN"
  else
    echo "No se encontró gunicorn en .venv ni en el sistema. Instálalo con: source .venv/bin/activate && pip install gunicorn" >&2
    exit 1
  fi
fi

export DJANGO_SETTINGS_MODULE="proyecto_rc.settings"
export PYTHONPATH="$ROOT_DIR"

echo "Iniciando gunicorn en 0.0.0.0:8000 (workers=3)..."
exec "$GUNICORN_BIN" proyecto_rc.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --log-level info \
  --access-logfile "-" \
  --error-logfile "-"
