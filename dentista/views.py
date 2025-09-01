from django.shortcuts import render

def dashboard(request):
    return render(request, "dentista/dashboard.html")

def agenda(request):
    return render(request, "dentista/agenda.html")

def pacientes(request):
    return render(request, "dentista/pacientes.html")
