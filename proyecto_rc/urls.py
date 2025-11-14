# proyecto_rc/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns 
from django.views.generic import TemplateView

# --- IMPORTS PARA JWT (API MÓVIL) ---
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
# --- FIN IMPORTS ---


urlpatterns = [
    # Ruta técnica necesaria para que funcione el cambio de idioma
    path("i18n/", include("django.conf.urls.i18n")),

    # --- RUTA CLAVE: CONECTAR LA APP 'API' ---
    path('api/', include('api.urls')), 
    # -----------------------------------------

    # Autenticación Social (Allauth)
    path('social/', include('allauth.urls')),

    # API MÓVIL (JWT Login)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# --- RUTAS CON PREFIJO DE IDIOMA (Tu Web) ---
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="landing/index.html"), name="home"),
    
    path("accounts/", include("accounts.urls")),
    path("paciente/", include("paciente.urls")),
    path("dentista/", include("dentista.urls")),
    
    prefix_default_language=False
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)