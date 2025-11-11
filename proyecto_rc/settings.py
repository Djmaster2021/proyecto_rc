from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-UNSAFE")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,.pythonanywhere.com"
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000,https://*.pythonanywhere.com"
).split(",")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",

    # Mis Apps
    "accounts",
    "api",
    "dentista",
    "domain",
    "paciente",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # OJO: LocaleMiddleware debe ir después de Session y antes de Common
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "proyecto_rc.urls"

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
                # Añadimos este para que las plantillas sepan el idioma actual
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "proyecto_rc.wsgi.application"

# MySQL vía PyMySQL
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

if os.getenv("MYSQL_DB_NAME") or True:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "consultorio_rc_test",
            "USER": "root",
            "PASSWORD": os.getenv("MYSQL_ROOT_PASSWORD", "root"),
            "HOST": "127.0.0.1",
            "PORT": "3307",
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- CONFIGURACIÓN INTERNACIONALIZACIÓN (I18N) ---
LANGUAGE_CODE = "es" # Idioma por defecto

LANGUAGES = [
    ('es', _('Español')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- CONFIGURACIÓN DE CORREO REAL (GMAIL SMTP) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# Leemos los valores secretos desde el archivo .env
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
# Usamos una f-string para combinar el nombre bonito con el correo real
DEFAULT_FROM_EMAIL = f'Consultorio Dental RC <{EMAIL_HOST_USER}>'
LOGIN_URL = "/accounts/login/"


LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "accounts:login"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# MERCADOPAGO CONFIG
# Le decimos a Django que lea estas variables de tu archivo .env
MERCADOPAGO_PUBLIC_KEY = os.getenv('MP_PUBLIC_KEY')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}