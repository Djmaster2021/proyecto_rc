# proyecto_rc/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView

# --- IMPORTS PARA JWT ---
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# --- IMPORTS NECESARIOS PARA LOGIN PERSONALIZADO ---
from accounts.views import CustomLoginView, redirect_by_role


urlpatterns = [
    # Cambio de idioma
    path("i18n/", include("django.conf.urls.i18n")),

    # API REST del proyecto
    path("api/", include("api.urls")),

    # Autenticación social (Google)
    path("social/", include("allauth.urls")),

    # JWT (API móvil)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]


# ===============================
#  RUTAS NORMALES (MULTI-IDIOMA)
# ===============================
urlpatterns += i18n_patterns(

    # ADMIN
    path("admin/", admin.site.urls),

    # LANDING PAGE
    path(
        "",
        TemplateView.as_view(template_name="landing/index.html"),
        name="home",
    ),

    # ========== ACCOUNTS ==========
    # Login personalizado (usuario/contraseña)
    path("accounts/login/", CustomLoginView.as_view(), name="account_login"),

    # Redirección universal post-login (Google y normal)
    path("accounts/post-login/", redirect_by_role, name="redirect_by_role"),

    # Rutas propias de accounts (registro, reset password, etc.)
    path(
        "accounts/",
        include(("accounts.urls", "accounts"), namespace="accounts"),
    ),

    # ========== APPS PRINCIPALES ==========
    path("paciente/", include("paciente.urls")),
    path("dentista/", include("dentista.urls")),

    prefix_default_language=False,
)


# STATIC & MEDIA
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
