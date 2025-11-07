from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # Portada pública (usa tu archivo existente en templates/landing/index.html)
    path("", TemplateView.as_view(template_name="landing/index.html"), name="home"),

    # Apps
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("dentista/", include(("dentista.urls", "dentista"), namespace="dentista")),
    path("paciente/", include(("paciente.urls", "paciente"), namespace="paciente")),
    path("api/", include(("api.urls", "api"), namespace="api")),

    # Admin
    path("admin/", admin.site.urls),
]
