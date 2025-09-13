# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    """
    Autentica y redirige según rol seleccionado en el formulario:
    - 'paciente'  -> /paciente/
    - 'dentista'  -> /dentista/
    """
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        role     = (request.POST.get("role") or "").strip()

        # Validación mínima por servidor (evita envío vacío)
        if not username or not password or not role:
            messages.error(request, "Complete usuario, contraseña y rol.")
            return render(request, "accounts/login.html")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "accounts/login.html")

        login(request, user)

        # Redirección por rol del formulario
        if role == "paciente":
            return redirect("/paciente/")
        if role == "dentista":
            return redirect("/dentista/")

        # Valor inesperado -> a inicio
        return redirect("/")

    return render(request, "accounts/login.html")
