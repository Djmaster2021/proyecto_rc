from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad / despliegue ---
SECRET_KEY = "django-insecure-CHANGE-ME"
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".pythonanywhere.com"]
CSRF_TRUSTED_ORIGINS = ["https://*.pythonanywhere.com"]

# --- Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # API
    "rest_framework",
    "rest_framework.authtoken",
    # CORS
    "corsheaders",
    # Apps del proyecto
    "domain",
    "api",
    "paciente",
    "dentista",
    "accounts",
]

# --- Middleware ---
MIDDLEWARE = [
    # CORS debe ir MUY arriba
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "proyecto_rc.urls"

# --- Templates ---
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
            ],
        },
    }
]

WSGI_APPLICATION = "proyecto_rc.wsgi.application"

# --- Base de datos: MySQL obligatorio (PythonAnywhere) ---
import os
MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")
MYSQL_DB_USER = os.getenv("MYSQL_DB_USER")
MYSQL_DB_PASSWORD = os.getenv("MYSQL_DB_PASSWORD")
MYSQL_DB_HOST = os.getenv("MYSQL_DB_HOST")
MYSQL_DB_PORT = os.getenv("MYSQL_DB_PORT", "3306")

_missing = [k for k,v in {
    "MYSQL_DB_NAME": MYSQL_DB_NAME,
    "MYSQL_DB_USER": MYSQL_DB_USER,
    "MYSQL_DB_PASSWORD": MYSQL_DB_PASSWORD,
    "MYSQL_DB_HOST": MYSQL_DB_HOST,
}.items() if not v]

if _missing:
    # Rompe en arranque si faltan variables: evita usar sqlite por accidente
    raise RuntimeError(f"Faltan variables MySQL: {', '.join(_missing)}")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": MYSQL_DB_NAME,
        "USER": MYSQL_DB_USER,
        "PASSWORD": MYSQL_DB_PASSWORD,
        "HOST": MYSQL_DB_HOST,
        "PORT": MYSQL_DB_PORT,
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"
        },
        "CONN_MAX_AGE": 600,
    }
}



# --- Passwords ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N / TZ ---
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos / media ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}

# --- CORS (permitimos subdominios PA + local) ---
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.pythonanywhere\.com$",
    r"^http://localhost(:\d+)?$",
    r"^https://localhost(:\d+)?$",
]
CORS_ALLOW_CREDENTIALS = True  # para cookies de sesión

# --- Endurecimiento producción (PA sirve HTTPS en subdominio) ---
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
