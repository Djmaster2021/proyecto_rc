# proyecto_rc/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # landing / home
    path("", TemplateView.as_view(template_name="landing/index.html"), name="home"),

    # apps (uso de include con namespace consistente)
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("dentista/", include(("dentista.urls", "dentista"), namespace="dentista")),
    path("paciente/", include(("paciente.urls", "paciente"), namespace="paciente")),
    path("api/", include(("api.urls", "api"), namespace="api")),
    path("domain/", include(("domain.urls", "domain"), namespace="domain")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
