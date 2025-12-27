# Runbook despliegue (Cloudflare + Django)

1) Variables/entorno
- `.env` con `DJANGO_DEBUG=False`, `SITE_BASE_URL=https://app.consultoriorc.org`, `DJANGO_ALLOWED_HOSTS` incluyendo dominio, `DJANGO_CSRF_TRUSTED_ORIGINS` con https, credenciales de DB/SMTP/Google/MercadoPago. Opcional `HEALTH_TOKEN` para health extendido.
- Si quieres logs JSON en prod, instala deps (vienen en requirements) y define `LOG_JSON=1`.
- En `ops/env.prod.example` tienes plantilla; no uses `.env` en el repo.

2) Base de datos
- Ejecuta migraciones: `.venv/bin/python manage.py migrate` con la DB apuntando al MySQL de prod.

3) Aplicación
- Arranca Gunicorn/Uvicorn (o `runserver` solo en dev). Si usas túnel, apunta al puerto backend (ej. 8001).
- Recolecta estáticos si aplica: `.venv/bin/python manage.py collectstatic --no-input`.

4) Cloudflare Tunnel
- Config en `~/.cloudflared/config.yml`:
  ```
  tunnel: consultoriorc
  credentials-file: /home/diego/.cloudflared/<id>.json
  ingress:
    - hostname: app.consultoriorc.org
      service: http://127.0.0.1:8001
    - service: http_status:404
  ```
- Levanta: `cloudflared tunnel run consultoriorc`. Verifica que esté “Connected”.

5) Google OAuth
- Redirects autorizados en consola Google: `https://app.consultoriorc.org/social/google/login/callback/` y `/accounts/google/login/callback/`.
- Ejecuta `python manage.py setup_google_socialapp` con envs `GOOGLE_OAUTH_CLIENT_ID/SECRET` cargadas.

6) Salud/monitoreo
- Health básico: `GET https://app.consultoriorc.org/api/health/`.
- Health extendido: añade header `X-HEALTH-TOKEN: <HEALTH_TOKEN>` para recibir `allowed_hosts` y configuración. Úsalo en monitores externos.
- Monitor externo sugerido: usar UptimeRobot/BetterStack apuntando a `/api/health/?token=<HEALTH_TOKEN>` con alerta si status != 200.

7) Checklist rápido
- ¿HTTPS activo? (Cloudflare proxy + certificado).
- ¿`SECURE_PROXY_SSL_HEADER` habilitado si hay proxy/túnel? (por defecto True con DEBUG=False).
- ¿`ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` incluyen el dominio?
- ¿`cloudflared` corriendo y apuntando al puerto correcto?
- ¿Redirects de Google coinciden con `SITE_BASE_URL`?

8) Apagar
- `ops/dev_down.sh` puede parar DB de dev y túnel; en prod detén el servicio systemd/supervisor correspondiente (Gunicorn, cloudflared) de forma ordenada.
