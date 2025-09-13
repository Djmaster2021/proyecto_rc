# paciente/views.py
from django.http import HttpResponse
from django.shortcuts import render


def dashboard(request):
    return render(request, "paciente/base.html")

def dashboard(request):
    return render(request, "paciente/dashboard.html")

def agendar_placeholder(request):
    return HttpResponse("Pantalla de agendar (placeholder).")

def reprogramar_placeholder(request, cita_id):
    return HttpResponse(f"Reprogramar cita {cita_id} (placeholder).")

def cancelar_placeholder(request, cita_id):
    return HttpResponse(f"Cancelar cita {cita_id} (placeholder).")

