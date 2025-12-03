from pathlib import Path
import os
import sys
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

# ====================================
# 1. CARGA DE ENTORNO
# ====================================

# Construye las rutas dentro del proyecto: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde el archivo .env
# Esto es vital para que lea tu contraseña de correo
load_dotenv(BASE_DIR / ".env")

# ====================================
# 2. SEGURIDAD Y DEBUG
# ====================================

# Si no encuentra la variable, por seguridad asume False en producción
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-key-default-change-me")

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS", 
    "http://127.0.0.1:8000,http://localhost:8000"
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
    "accounts",
    "api",
    "dentista",
    "domain",
    "paciente",
]

SITE_ID = 1

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
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")

# Servidor de Gmail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"

# Credenciales leídas EXACTAMENTE del .env
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
# Toggle global para evitar envíos reales en desarrollo
SEND_EMAILS = os.getenv("DJANGO_SEND_EMAILS", "true").lower() == "true"
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")

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
LOGIN_REDIRECT_URL = "/dentista/dashboard/" 
LOGOUT_REDIRECT_URL = "/accounts/login/"

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"

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
    )
}

# MercadoPago
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY", "")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")

# Google Calendar API
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOOGLE_CALENDAR_CLIENT_CONFIG_FILE = BASE_DIR / "google_credentials" / "credentials.json"
GOOGLE_CALENDAR_TOKEN_FILE = BASE_DIR / "google_credentials" / "token.json"
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")
