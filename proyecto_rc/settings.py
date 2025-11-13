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
    
    # --- REQUERIDO POR ALLAUTH ---
    "django.contrib.sites",  # Necesario
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google", # Proveedor de Google
    # -----------------------------

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
    # --- MIDDLEWARE DE ALLAUTH (Recomendado para nuevas versiones) ---
    "allauth.account.middleware.AccountMiddleware", 
    # -----------------------------------------------------------------
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
                "django.template.context_processors.i18n",
                # Requerido por allauth para acceder al request en templates
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
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = f'Consultorio Dental RC <{EMAIL_HOST_USER}>'

# --- CONFIGURACIÓN DE LOGIN Y ALLAUTH ---

# 1. ID del sitio (Requerido por django.contrib.sites)
SITE_ID = 1

# 2. Backends de autenticación
AUTHENTICATION_BACKENDS = [
    # Necesario para entrar al admin de Django con usuario/pass
    'django.contrib.auth.backends.ModelBackend',
    # Específico de Allauth (para entrar con Google/Email)
    'allauth.account.auth_backends.AuthenticationBackend',
]

# 3. Configuración de comportamiento
LOGIN_URL = "/accounts/login/" 
# ¡AQUÍ ESTÁ EL CAMBIO IMPORTANTE!
# Redirigimos al 'dashboard' general para que el router decida a dónde vas
LOGIN_REDIRECT_URL = "/accounts/dashboard/" 
LOGOUT_REDIRECT_URL = "accounts:login"

# Ajustes de Allauth
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# 4. Configuración del Proveedor (Google)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# 5. TU ADAPTADOR PERSONALIZADO
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.MySocialAccountAdapter'


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# MERCADOPAGO CONFIG
#MERCADOPAGO_PUBLIC_KEY = os.getenv('MP_PUBLIC_KEY')
#MERCADOPAGO_ACCESS_TOKEN = "TEST-32657..."


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

MERCADOPAGO_PUBLIC_KEY = "APP_USR-106817ba-8964-493f-ac1e-378be13ca6e6"
MERCADOPAGO_ACCESS_TOKEN = "APP_USR-326579153327013-110820-c53486ce36e9b4b0db2cae68b143dc3e-2974333049"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'