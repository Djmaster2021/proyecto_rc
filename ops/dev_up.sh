#!/usr/bin/env bash
set -euo pipefail

# Arranca base de datos, túnel de Cloudflare (consultoriorc) y servidor Django.
# Úsalo desde la raíz del repo: ops/dev_up.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env" ]; then
  echo "[dev] Falta .env. Copia .env.example y completa credenciales."
  exit 1
fi

echo "[dev] Levantando base de datos (docker compose up -d db)..."
docker compose up -d db

if command -v cloudflared >/dev/null 2>&1; then
  if pgrep -f "cloudflared tunnel run consultoriorc" >/dev/null 2>&1; then
    echo "[dev] cloudflared ya está corriendo para consultoriorc."
  else
    echo "[dev] Iniciando cloudflared (consultoriorc)... logs: /tmp/cloudflared-consultoriorc.log"
    cloudflared tunnel run consultoriorc >/tmp/cloudflared-consultoriorc.log 2>&1 &
    echo $! > /tmp/cloudflared-consultoriorc.pid
  fi
else
  echo "[dev] cloudflared no está instalado. Salta el túnel (usa http local)."
fi

echo "[dev] Iniciando servidor Django en 0.0.0.0:8001..."
exec .venv/bin/python manage.py runserver 0.0.0.0:8001
