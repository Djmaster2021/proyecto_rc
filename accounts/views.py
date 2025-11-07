from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import PacienteRegisterForm  # <-- Importamos nuestro formulario pulido
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, get_user_model
from typing import Optional

# --- Lógica de Login (tuya, mejorada) ---

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

class LoginAndRedirectView(View):
    template_name = "accounts/login.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {"next": request.GET.get("next")})

    def post(self, request: HttpRequest) -> HttpResponse:
        role = request.POST.get("role", "paciente")
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        next_url = _safe_next(request.POST.get("next")) or _safe_next(request.GET.get("next"))

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, self.template_name, {"next": next_url, "role": role, "username": username})

        login(request, user)
        if next_url:
            return redirect(next_url)
        
        # Redirigir según rol elegido
        dest = ROLE_TO_URL.get(role, "/paciente/")
        return redirect(dest)


# --- Vista de Logout ---
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión exitosamente.")
    # Usamos reverse_lazy en lugar de reverse para evitar importación circular
    return redirect(reverse_lazy('accounts:login')) 


# --- ¡AQUÍ ESTÁ LA VISTA DE REGISTRO PULIDA! ---
# Esto define el RegisterView que tu urls.py ya está importando.

class RegisterView(CreateView):
    """
    Vista basada en clase para registrar un nuevo Paciente.
    Usa el formulario 'PacienteRegisterForm' que creamos.
    """
    form_class = PacienteRegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login') # A dónde ir después del registro

    def form_valid(self, form):
        """
        Esto se llama cuando el formulario es válido.
        El .save() de nuestro formulario ya hace toda la magia.
        """
        response = super().form_valid(form)
        messages.success(self.request, f"¡Cuenta creada! Ya puedes iniciar sesión.")
        return response

    def form_invalid(self, form):
        """
        Esto se llama si el formulario no es válido (ej. contraseñas no coinciden)
        """
        # El formulario ya trae los errores, solo mostramos un mensaje general
        messages.error(self.request, "Error al registrarse. Por favor, revisa los datos.")
        return super().form_invalid(form)