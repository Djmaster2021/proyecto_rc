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

    # --- API MÓVIL (JWT Login) ---
    # Endpoint para que la app móvil obtenga un token (Login)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Endpoint para que la app móvil refresque un token expirado
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # (Eventualmente, aquí también conectarás las URLs de tu app 'api')
    # path('api/', include('api.urls')),
    # --- FIN API MÓVIL ---
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="landing/index.html"), name="home"),
    path("accounts/", include("accounts.urls")),
    path("paciente/", include("paciente.urls")),
    path("dentista/", include("dentista.urls")),
    
    # OPCIÓN PROFESIONAL: False = Español en raíz (/), Inglés con prefijo (/en/)
    prefix_default_language=False
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)