# proyecto_rc/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Landing pública (fuera de las apps)
    path("", TemplateView.as_view(template_name="landing/index.html"), name="home"),

    # Frontends por sección
    path("dentista/", include("dentista.urls")),   # -> dentista:...
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("paciente/", include(("paciente.urls", "paciente"), namespace="paciente")),
]
