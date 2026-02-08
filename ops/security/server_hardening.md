# Server Hardening Checklist (Linux)

## 1. Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 3306/tcp
sudo ufw enable
sudo ufw status verbose
```

## 2. Fail2ban
Instala fail2ban y crea un jail para Nginx/SSH:
```bash
sudo apt-get update && sudo apt-get install -y fail2ban
```

Archivo sugerido `/etc/fail2ban/jail.d/proyecto_rc.local`:
```ini
[sshd]
enabled = true
maxretry = 5
bantime = 1h

[nginx-http-auth]
enabled = true
maxretry = 10
bantime = 1h

[nginx-botsearch]
enabled = true
maxretry = 10
bantime = 1h
```

Reinicia:
```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status
```

## 3. Servicios con systemd
- Ejecuta `gunicorn` y `cloudflared/nginx` como servicios.
- `Restart=always`.
- Usuario no-root dedicado.

## 4. Backups y restauracion
- Backup diario de DB con retencion minima de 7-14 dias.
- Cifrar y enviar a almacenamiento externo.
- Prueba restauracion semanal (obligatorio).

Ejemplo:
```bash
mysqldump -u consultorio_app -p consultorio_rc | gzip > /var/backups/consultorio_rc_$(date +%F).sql.gz
```

## 5. Actualizaciones y CVEs
- Activar actualizaciones de seguridad del sistema.
- Ejecutar auditoria de paquetes Python:
```bash
pip install pip-audit
pip-audit
```

## 6. Observabilidad minima
- Monitorear `5xx`, `403`, `429`, latencia y errores de login.
- Alertar cuando haya picos de rechazo o caida de `/api/health/`.
