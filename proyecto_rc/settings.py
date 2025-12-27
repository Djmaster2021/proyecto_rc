from pathlib import Path
import os
import sys
import importlib.util
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _
from urllib.parse import urlparse

# ====================================
# 1. CARGA DE ENTORNO
# ====================================

# Construye las rutas dentro del proyecto: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno: primero secrets/.env.private si existe, si no .env
private_env = BASE_DIR / "secrets" / ".env.private"
env_file = private_env if private_env.exists() else BASE_DIR / ".env"
load_dotenv(env_file)

# ====================================
# 2. SEGURIDAD Y DEBUG
# ====================================

# Si no encuentra la variable, por seguridad asume False en producción
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    # Evitar que el servidor arranque con una llave insegura en prod
    if DEBUG:
        SECRET_KEY = "django-insecure-key-default-change-me"
    else:
        raise RuntimeError("Configura DJANGO_SECRET_KEY en el entorno para producción.")

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,10.0.2.2").split(",")
if DEBUG:
    for host in ("0.0.0.0", "10.0.2.2"):
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
# Añadimos el host derivado de SITE_BASE_URL para evitar errores DisallowedHost
site_base = os.getenv("SITE_BASE_URL")
if site_base:
    netloc = urlparse(site_base).netloc or site_base
    host_only = netloc.split(":")[0]
    for h in (netloc, host_only):
        if h and h not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(h)

CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS", 
    "http://127.0.0.1:8000,http://localhost:8000,https://127.0.0.1:8000,https://localhost:8000"
).split(",")

# ====================================
# 3. APLICACIONES INSTALADAS
# ====================================

INSTALLED_APPS = [
    # Core Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # Requerido por allauth

    # Librerías de terceros
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",

    # Tus aplicaciones
    "accounts.apps.AccountsConfig",
    "api",
    "dentista",
    "domain",
    "paciente",
]

SITE_ID = 1
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

# ====================================
# 4. MIDDLEWARE
# ====================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "proyecto_rc.middleware.HostLoggingMiddleware",
]

ROOT_URLCONF = "proyecto_rc.urls"

# ====================================
# 5. TEMPLATES (HTML)
# ====================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                # Procesadores de contexto personalizados
                "paciente.context_processors.penalizacion_paciente", 
            ],
        },
    },
]

WSGI_APPLICATION = "proyecto_rc.wsgi.application"

# ====================================
# 6. BASE DE DATOS (MySQL)
# ====================================

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DB_NAME", "consultorio_rc"),
        "USER": os.getenv("MYSQL_DB_USER", "root"),
        "PASSWORD": os.getenv("MYSQL_DB_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_DB_PORT", "3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Para ejecutar tests sin requerir permisos CREATE en MySQL,
# usamos SQLite cuando el comando incluye "test".
if "test" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }

# ====================================
# 7. VALIDACIÓN DE PASSWORD
# ====================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ====================================
# 8. CONFIGURACIÓN DE CORREO (SMTP - GMAIL)
# ====================================

# Usamos SMTP para enviar correos reales
# Backend real para enviar correos
# Backend de correo: en desarrollo usamos consola para no enviar reales
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)

# Servidor de Gmail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"

# Credenciales leídas EXACTAMENTE del .env
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
# Toggle global para evitar envíos reales en desarrollo
SEND_EMAILS = os.getenv(
    "DJANGO_SEND_EMAILS",
    "false" if DEBUG else "true",
).lower() == "true"
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "")

# Remitente por defecto
# ====================================
# 9. INTERNACIONALIZACIÓN
# ====================================

LANGUAGE_CODE = "es"

LANGUAGES = [
    ("es", _("Español")),
    ("en", _("English")),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# ====================================
# 10. ARCHIVOS ESTÁTICOS Y MEDIA
# ====================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ====================================
# 11. AUTH / LOGIN / ALLAUTH
# ====================================

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Redirecciones
LOGIN_URL = "/accounts/login/"
# Cambia esto si quieres que al loguearse vayan directo al dashboard
LOGIN_REDIRECT_URL = "/accounts/redirect-by-role/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Allauth (login por usuario o email, evita settings deprecados)
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["username", "email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGOUT_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

ACCOUNT_ADAPTER = "accounts.adapters.MyAccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.MySocialAccountAdapter"

# ====================================
# 12. CONFIGURACIÓN EXTRA (API, PAGOS, CALENDARIO)
# ====================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF / JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Solo autenticados por defecto; abre endpoints puntuales con AllowAny.
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # Limitamos llamadas básicas para evitar abuso en endpoints abiertos (chatbot/slots).
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_THROTTLE_ANON", "50/min"),
        "user": os.getenv("DRF_THROTTLE_USER", "200/min"),
    },
}

# MercadoPago
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY", "")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
MERCADOPAGO_TEST_PAYER_EMAIL = os.getenv("MERCADOPAGO_TEST_PAYER_EMAIL", "")
# Si está en '1'/'true', simula pago exitoso (solo sandbox/desarrollo)
MERCADOPAGO_FAKE_SUCCESS = os.getenv("MERCADOPAGO_FAKE_SUCCESS", "0").lower() in ("1", "true", "yes")
# Desactiva el fake en pruebas automatizadas para no romper asserts
if "test" in sys.argv:
    MERCADOPAGO_FAKE_SUCCESS = False
MERCADOPAGO_WEBHOOK_SECRET = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "")

# Google Calendar API
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOOGLE_CALENDAR_CLIENT_CONFIG_FILE = BASE_DIR / "google_credentials" / "credentials.json"
GOOGLE_CALENDAR_TOKEN_FILE = BASE_DIR / "google_credentials" / "token.json"
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

# Chatbot IA (Gemini opcional)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
CHATBOT_MAX_CONTEXT = int(os.getenv("CHATBOT_MAX_CONTEXT", "3"))
# Auto-enciende IA si hay API key, a menos que el flag explícito diga lo contrario.
_CHATBOT_FLAG = os.getenv("CHATBOT_IA_ENABLED")
if _CHATBOT_FLAG is None:
    CHATBOT_IA_ENABLED = bool(GEMINI_API_KEY)
else:
    CHATBOT_IA_ENABLED = _CHATBOT_FLAG.lower() in ("1", "true", "yes")
# API Chatbot (opcional): si se define, exige header X-CHATBOT-SECRET
CHATBOT_API_SECRET = os.getenv("CHATBOT_API_SECRET", "")

# ====================================
# 13. SEGURIDAD HTTP (opcional)
# ====================================

def _env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw.lower() in ("1", "true", "yes")

_secure_default = not DEBUG
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", _secure_default)
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", _secure_default)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if _secure_default else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", _secure_default)
SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", False if DEBUG else True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if _env_bool("SECURE_PROXY_SSL_HEADER", _secure_default) else None
USE_X_FORWARDED_HOST = _env_bool("USE_X_FORWARDED_HOST", _secure_default)
SECURE_CONTENT_TYPE_NOSNIFF = _env_bool("SECURE_CONTENT_TYPE_NOSNIFF", True)
SECURE_REFERRER_POLICY = os.getenv("SECURE_REFERRER_POLICY", "same-origin")
X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")
CSRF_COOKIE_HTTPONLY = _env_bool("CSRF_COOKIE_HTTPONLY", True)

# ====================================
# 14. CACHE (para throttling y webhooks)
# ====================================
# En prod usa Redis/Memcached; aquí dejamos LocMem por defecto.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "proyecto-rc-cache",
    }
}

# ====================================
# 15. LOGGING
# ====================================

_use_json_logs = _env_bool("LOG_JSON", not DEBUG)
_has_jsonlogger = importlib.util.find_spec("pythonjsonlogger") is not None
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        **(
            {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            }
            if _has_jsonlogger
            else {}
        ),
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if (_use_json_logs and _has_jsonlogger) else "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "proyecto_rc.requests": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
