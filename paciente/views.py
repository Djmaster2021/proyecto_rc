from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

@login_required
def dashboard(request):
    """
    Dashboard principal del paciente.
    Solo accesible si estás logueado Y tienes un perfil de paciente.
    """
    if not hasattr(request.user, 'perfil_paciente'):
        messages.error(request, "No tienes permiso para acceder a esta área.")
        return redirect('home') 
    
    paciente = request.user.perfil_paciente
    context = {
        'paciente': paciente,
    }
    return render(request, "paciente/dashboard.html", context)

@login_required
def citas(request):
    return render(request, "paciente/citas.html")

@login_required
def pagos(request):
    return render(request, "paciente/pagos.html")

# --- Vistas Placeholder (Necesarias para que urls.py no falle por ahora) ---

@login_required
def agendar_placeholder(request):
    return HttpResponse("Próximamente: Pantalla de Agendar Cita Real")

@login_required
def reprogramar_placeholder(request, cita_id):
    return HttpResponse(f"Próximamente: Reprogramar cita {cita_id}")

@login_required
def cancelar_placeholder(request, cita_id):
    return HttpResponse(f"Próximamente: Cancelar cita {cita_id}")