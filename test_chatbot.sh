#!/usr/bin/env bash
# Test rápido del chatbot (requiere servidor corriendo en localhost:8000).
set -euo pipefail

URL=${1:-http://127.0.0.1:8000/api/chatbot/}
QUERY=${2:-"Quiero agendar mañana a las 10"}

echo ">>> Enviando a ${URL}"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"${QUERY}\"}" \
  "${URL}" | python -m json.tool
