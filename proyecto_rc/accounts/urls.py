from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Monta accounts con namespace
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Rutas de tus otras apps...
    path('dentista/', include('dentista.urls')),
    path('paciente/', include('paciente.urls')),
    # path('', include('proyecto_rc.urls')),  # si usas landing
]
