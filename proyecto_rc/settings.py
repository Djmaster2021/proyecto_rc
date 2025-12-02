from pathlib import Path
import os

from django.urls import reverse_lazy
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

# ====================================
# BASE
# ====================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ====================================
# DEBUG / SECRET_KEY
# ====================================

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

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

# ====================================
# APPS
# ====================================

INSTALLED_APPS = [
    # Core Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # allauth
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # DRF / JWT
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",

    # Apps del proyecto
    "accounts",
    "api",
    "dentista",
    "domain",
    "paciente",
]

SITE_ID = 1

# ====================================
# MIDDLEWARE
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
# TEMPLATES
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
                # Procesador de contexto para penalizaciones (si existe)
                # "paciente.context_processors.penalizacion_paciente", 
            ],
        },
    },
]

WSGI_APPLICATION = "proyecto_rc.wsgi.application"

# ====================================
# BASE DE DATOS (MySQL vía PyMySQL)
# ====================================

try:
    import pymysql  # type: ignore
    pymysql.install_as_MySQLdb()
except Exception:
    pass

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

# ====================================
# PASSWORD VALIDATORS
# ====================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ====================================
# INTERNATIONALIZATION
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
# STATIC / MEDIA
# ====================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ====================================
# EMAIL (SMTP)
# ====================================

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Consultorio RC <no-reply@consultoriorc.com>",
)

# ====================================
# AUTH / LOGIN / ALLAUTH
# ====================================

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Redirecciones
LOGIN_URL = "/accounts/login/"
LOGOUT_REDIRECT_URL = "/"  # Al salir, va al home

# IMPORTANTE: Aquí activamos al Policía de Tráfico
LOGIN_REDIRECT_URL = "/redireccionar-usuario/"

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
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
# DEFAULT AUTO FIELD
# ====================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ====================================
# DRF / JWT
# ====================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )
}

# ====================================
# MERCADOPAGO & GOOGLE CALENDAR
# ====================================

MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY", "")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")

GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOOGLE_CALENDAR_CLIENT_CONFIG_FILE = BASE_DIR / "google_credentials" / "credentials.json"
GOOGLE_CALENDAR_TOKEN_FILE = BASE_DIR / "google_credentials" / "token.json"
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "dentista.choyo@gmail.com")