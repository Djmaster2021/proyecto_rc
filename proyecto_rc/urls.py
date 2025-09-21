from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # URL para tu página de inicio (landing page)
    path("", TemplateView.as_view(template_name="landing/index.html"), name="home"),

    # --- INCLUSIÓN DE URLS DE LAS APPS ---
    path('dentista/', include('dentista.urls', namespace='dentista')),

    # Otras apps
    path("paciente/", include("paciente.urls")),
    path("accounts/", include("accounts.urls")),
]

# Servir estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
