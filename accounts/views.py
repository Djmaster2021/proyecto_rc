from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import PacienteRegisterForm
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required # <-- Importante importar esto
from typing import Optional

# --- Lógica de Login (Login manual) ---

ROLE_TO_URL = {
    "admin": "/admin/",
    "dentista": "/dentista/",
    "paciente": "/paciente/",
}

def _safe_next(next_param: Optional[str]) -> Optional[str]:
    if not next_param:
        return None
    if next_param.startswith("/") and not next_param.startswith("//"):
        return next_param
    return None

class LoginAndRedirectView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True 

    def get_success_url(self):
        """
        Esta función se ejecuta en login MANUAL.
        """
        user = self.request.user
        
        if hasattr(user, 'perfil_dentista'):
            return '/dentista/' 
        
        if hasattr(user, 'perfil_administrador'):
             return '/admin/dashboard/' 
             
        if user.is_superuser:
            return '/admin/'

        return '/paciente/'

# --- Vista de Logout ---
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect(reverse_lazy('accounts:login')) 


# --- Vista de Registro ---

class RegisterView(CreateView):
    form_class = PacienteRegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login') 

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"¡Cuenta creada! Ya puedes iniciar sesión.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Error al registrarse. Por favor, revisa los datos.")
        return super().form_invalid(form)


# --- NUEVA VISTA: ROUTER INTELIGENTE (SEMÁFORO) ---
# Esta es la vista que soluciona el problema de "Acceso restringido"

@login_required
def dashboard_redirect(request):
    """
    Esta vista actúa como un semáforo.
    Se ejecuta después del login de Google (o login genérico).
    Revisa quién eres y te manda a tu casa.
    """
    user = request.user

    # 1. Si es Superusuario o Staff -> Admin de Django
    if user.is_superuser or user.is_staff:
        return redirect('/admin/')

    # 2. Si pertenece al grupo Dentistas -> Panel Dentista
    # (También verificamos el perfil por si acaso)
    if user.groups.filter(name='Dentistas').exists() or hasattr(user, 'perfil_dentista'):
        return redirect('/dentista/') 

    # 3. Si pertenece al grupo Pacientes -> Panel Paciente
    if user.groups.filter(name='Pacientes').exists() or hasattr(user, 'perfil_paciente'):
        return redirect('/paciente/')
    
    # 4. Fallback: Si no tiene grupo claro, asumimos que es un Paciente nuevo
    # (esto pasa con Google antes de que se asignen otros roles especiales)
    return redirect('/paciente/')