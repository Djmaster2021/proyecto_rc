from pathlib import Path
import os
from django.urls import reverse_lazy
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

# BASE
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# DEBUG / SECRET_KEY
DEBUG = True

SECRET_KEY = (
    os.getenv("DJANGO_SECRET_KEY")
    or os.getenv("SECRET_KEY")
    or "dev-secret-key-consultorio-rc-2025-no-usar-en-produccion"
)

ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,.pythonanywhere.com",
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000,https://*.pythonanywhere.com",
).split(",")

# APPS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # --- REQUERIDO POR ALLAUTH ---
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # -----------------------------

    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",

    # Mis apps
    "accounts",
    "api",
    "dentista",
    "domain",
    "paciente",
]

# MIDDLEWARE
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

# TEMPLATES
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
                "paciente.context_processors.penalizacion_paciente",
            ],
        },
    },
]

WSGI_APPLICATION = "proyecto_rc.wsgi.application"

# BASE DE DATOS (MySQL vía PyMySQL)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DB_NAME", "consultorio_rc"),
        "USER": os.getenv("MYSQL_DB_USER", "user"),
        "PASSWORD": os.getenv("MYSQL_DB_PASSWORD", "password"),
        "HOST": os.getenv("MYSQL_DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_DB_PORT", "3307"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# VALIDADORES DE PASSWORD
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# INTERNACIONALIZACIÓN
LANGUAGE_CODE = "es"

LANGUAGES = [
    ("es", _("Español")),
    ("en", _("English")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# STATIC / MEDIA
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ============================
# CONFIGURACIÓN DE CORREO (CORREGIDA)
# ============================
# Usaremos la cuenta que ya tiene contraseña de aplicación válida
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Cuenta que ENVÍA los correos (Sistema)
EMAIL_HOST_USER = 'dentista.choyo@gmail.com' 
# Contraseña de Aplicación de esa cuenta
EMAIL_HOST_PASSWORD = 'dgsscdvsvwhtjfcz'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# LOGIN / ALLAUTH
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/post-login/"   # <- NUEVA RUTA
LOGOUT_REDIRECT_URL = "/accounts/login/"



# --- Configuración moderna de django-allauth ---
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_USERNAME_REQUIRED = False # Importante si usas solo email
ACCOUNT_EMAIL_REQUIRED = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

ACCOUNT_ADAPTER = "accounts.adapters.MyAccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.MySocialAccountAdapter"



DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF / JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )
}

# MERCADOPAGO
MERCADOPAGO_PUBLIC_KEY = "APP_USR-106817ba-8964-493f-ac1e-378be13ca6e6"
MERCADOPAGO_ACCESS_TOKEN = "APP_USR-326579153327013-110820-c53486ce36e9b4b0db2cae68b143dc3e-2974333049"

# GOOGLE CALENDAR
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]

GOOGLE_CALENDAR_CLIENT_CONFIG_FILE = BASE_DIR / "google_credentials" / "credentials.json"
GOOGLE_CALENDAR_TOKEN_FILE = BASE_DIR / "google_credentials" / "token.json"
GOOGLE_CALENDAR_ID = "dentista.choyo@gmail.com"