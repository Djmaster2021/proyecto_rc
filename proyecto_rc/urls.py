# proyecto_rc/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView, RedirectView
from django.shortcuts import redirect
from django.http import HttpResponse

# --- IMPORTS PARA JWT (API) ---
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# --- FUNCIÓN: POLICÍA DE TRÁFICO (Redirección Inteligente) ---
def redireccionar_usuario(request):
    """
    Esta función decide a dónde enviar al usuario después de iniciar sesión.
    """
    user = request.user
    
    # 1. Si no está logueado, al login
    if not user.is_authenticated:
        return redirect('account_login') # Usa el name de abajo
        
    # 2. Si es DENTISTA -> Dashboard del Dentista
    if hasattr(user, 'dentista'):
        return redirect('dentista:dashboard')
        
    # 3. Si es PACIENTE (y ya completó perfil) -> Dashboard Paciente
    if hasattr(user, 'paciente_perfil'):
        return redirect('paciente:dashboard')
        
    # 4. Si es NUEVO (Login con Google por primera vez) -> Completar Perfil
    return redirect('paciente:completar_perfil')


# ===============================
#  RUTAS TÉCNICAS (NO IDIOMA)
# ===============================
urlpatterns = [
    # Verificación de dominio para Google Search Console
    path(
        "google0c7f6f52abc015a8.html",
        lambda request: HttpResponse("google-site-verification: google0c7f6f52abc015a8.html"),
    ),
    # Vista personalizada para cuentas inactivas (sobre escribe la de allauth)
    path(
        "social/inactive/",
        TemplateView.as_view(template_name="account/account_inactive.html"),
        name="account_inactive",
    ),
    # Redirige login/signup de allauth a las rutas locales de accounts
    path(
        "social/login/",
        RedirectView.as_view(pattern_name="accounts:login", permanent=False),
        name="social_login_redirect",
    ),
    path(
        "social/signup/",
        RedirectView.as_view(pattern_name="accounts:register", permanent=False),
        name="social_signup_redirect",
    ),

    # Cambio de idioma
    path("i18n/", include("django.conf.urls.i18n")),

    # API REST del proyecto
    path("api/", include("api.urls")),

    # Autenticación social (Google)
    # Lo dejamos en 'social/' para que no choque con tus cuentas normales
    path("social/", include("allauth.urls")),

    # JWT (API móvil)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # RUTA MÁGICA DE REDIRECCIÓN
    path('redireccionar-usuario/', redireccionar_usuario, name='redireccionar_usuario'),
]

# ===============================
#  RUTAS VISUALES (MULTI-IDIOMA)
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

    # ========== ACCOUNTS (CORREGIDO) ==========
    # Quitamos la línea de allauth de aquí para que NO estorbe.
    # Ahora 'accounts/' apunta EXCLUSIVAMENTE a tu app personalizada.
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    
    # Ruta directa para el login (ayuda al redirect 'account_login')
    # Asegúrate de que en accounts/urls.py tengas un path con name='login'
    
    # ========== APPS PRINCIPALES ==========
    path("paciente/", include("paciente.urls")),
    path("dentista/", include("dentista.urls")),

    prefix_default_language=False,
)

# STATIC & MEDIA (Solo en modo DEBUG)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
