from django.shortcuts import render

def dashboard(request):
    """Muestra el panel principal del dentista."""
    return render(request, "dentista/dashboard.html")

def agenda(request):
    """Muestra la agenda de citas."""
    return render(request, "dentista/agenda.html")

def pacientes(request):
    """Muestra la lista de pacientes."""
    return render(request, "dentista/pacientes.html")

def pagos(request):
    """Muestra el historial de pagos."""
    return render(request, "dentista/pagos.html")

def servicios(request):
    """Muestra el catálogo de servicios."""
    return render(request, "dentista/servicios.html")

def reportes(request):
    """Muestra la página de reportes y estadísticas."""
    return render(request, "dentista/reportes.html")

def historial(request):
    """
    Muestra el historial detallado de un paciente específico.
    NOTA: En el futuro, esta vista recibirá un ID de paciente.
    """
    return render(request, "dentista/historial.html")

def vista_paciente(request):
    """Muestra la vista simplificada para el paciente."""
    return render(request, "dentista/vista-paciente.html")
