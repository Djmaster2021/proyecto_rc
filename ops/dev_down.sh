#!/usr/bin/env bash
set -euo pipefail

# Detiene túnel cloudflared y contenedor de base de datos.
# Úsalo desde la raíz del repo: ops/dev_down.sh

echo "[dev] Parando cloudflared (si estaba iniciado por dev_up)..."
if [ -f /tmp/cloudflared-consultoriorc.pid ]; then
  PID=$(cat /tmp/cloudflared-consultoriorc.pid || true)
  if [ -n "${PID}" ] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" || true
    echo "[dev] cloudflared detenido (pid $PID)."
  fi
  rm -f /tmp/cloudflared-consultoriorc.pid
else
  # fallback: intenta matar procesos con esa firma
  pkill -f "cloudflared tunnel run consultoriorc" 2>/dev/null || true
fi

echo "[dev] Deteniendo contenedor db (docker compose stop db)..."
docker compose stop db || true

echo "[dev] Listo."
