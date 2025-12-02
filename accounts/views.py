# accounts/views.py

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .forms import PacienteRegisterForm


# ==============================
# FUNCIÓN ÚNICA DE REDIRECCIÓN
# ==============================

def redirect_by_role(request):
    """
    Después de cualquier login (normal o Google), enviamos
    al usuario al panel correcto según su rol.
    """
    user = request.user

    if not user.is_authenticated:
        # Nombre de la URL de login (definida en urls.py como account_login)
        return redirect("account_login")

    # 1. Admin / staff -> panel de Django
    if user.is_superuser or user.is_staff or user.groups.filter(name="Administrador").exists():
        return redirect("/admin/")

    # 2. Dentista -> dashboard dentista
    if user.groups.filter(name="Dentista").exists():
        return redirect("dentista:dashboard")

    # 3. Paciente -> dashboard paciente
    if user.groups.filter(name="Paciente").exists():
        return redirect("paciente:dashboard")

    # 4. Sin rol -> home
    return redirect("home")


# ==============================
# LOGIN CON USUARIO / CONTRASEÑA
# ==============================

class CustomLoginView(LoginView):
    """
    Login con usuario/contraseña usando template accounts/login.html.
    Después del login, redirige por rol usando redirect_by_role.
    """
    template_name = "accounts/login.html"

    def get_success_url(self):
        # Mandamos siempre a la vista central de redirección
        return reverse("redirect_by_role")

    def form_invalid(self, form):
        messages.error(self.request, "Usuario o contraseña incorrectos. Intenta de nuevo.")
        return super().form_invalid(form)


# ==============================
# REGISTRO DE PACIENTES
# ==============================

def register(request):
    """
    Registro de pacientes (correo + contraseña).
    """
    if request.method == "POST":
        form = PacienteRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Asignar grupo Paciente
            paciente_group, _ = Group.objects.get_or_create(name="Paciente")
            user.groups.add(paciente_group)

            messages.success(
                request,
                "Tu cuenta ha sido creada correctamente. ¡Bienvenido!",
            )

            # Login directo y redirección al dashboard paciente
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("paciente:dashboard")
    else:
        form = PacienteRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def post_login(request):
    user = request.user

    # Si es paciente
    if hasattr(user, "perfil_paciente"):
        paciente = user.perfil_paciente

        # Si NO tiene teléfono, mandamos primero a completar perfil
        if not paciente.telefono:
            return redirect("paciente:completar_perfil")

        # Si ya está completo, directo al dashboard del paciente
        return redirect("paciente:dashboard")

    # Si es dentista
    if hasattr(user, "perfil_dentista"):
        return redirect("dentista:dashboard")

    # Cualquier otro caso
    return redirect("home")
