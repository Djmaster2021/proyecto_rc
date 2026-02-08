-- Ejecuta esto como usuario administrador de MySQL.
-- Ajusta valores de dominio/host/password antes de usar en producción.

-- 1) Usuario de app con privilegios mínimos sobre una sola base.
CREATE USER IF NOT EXISTS 'consultorio_app'@'127.0.0.1' IDENTIFIED BY 'CAMBIA_ESTA_PASSWORD_LARGA';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'consultorio_app'@'127.0.0.1';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP ON consultorio_rc.* TO 'consultorio_app'@'127.0.0.1';
FLUSH PRIVILEGES;

-- 2) Recomendaciones operativas (aplicar fuera de este script):
-- - No exponer MySQL en internet.
-- - bind-address=127.0.0.1 (o red privada interna).
-- - Desactivar root remoto.
-- - Rotar contraseñas periodicamente.
