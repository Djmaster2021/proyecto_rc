from django.shortcuts import render

def dashboard(request):
    return render(request, "paciente/dashboard.html")

def citas(request):
    return render(request, "paciente/citas.html")

def pagos(request):
    return render(request, "paciente/pagos.html")
