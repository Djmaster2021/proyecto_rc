from typing import Optional
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

User = get_user_model()

ROLE_TO_URL = {
    "admin": "/admin/",
    "dentista": "/dentista/",
    "paciente": "/paciente/",
}

def _safe_next(next_param: Optional[str]) -> Optional[str]:
    # No permitir redirecciones externas
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

        # Prioridad al ?next=
        if next_url:
            return redirect(next_url)

        # Redirigir según rol elegido
        dest = ROLE_TO_URL.get(role, "/paciente/")
        return redirect(dest)

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect(reverse("accounts:login"))

class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name)

    def post(self, request: HttpRequest) -> HttpResponse:
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        role = request.POST.get("role", "paciente")

        if not username or not password1:
            messages.error(request, "Usuario y contraseña son obligatorios.")
            return render(request, self.template_name, request.POST)

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, self.template_name, request.POST)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ese usuario ya existe.")
            return render(request, self.template_name, request.POST)

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return redirect(ROLE_TO_URL.get(role, "/paciente/"))
