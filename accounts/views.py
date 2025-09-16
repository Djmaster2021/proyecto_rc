from django.contrib import messages, auth
from django.shortcuts import render, redirect

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username') or ''
        password = request.POST.get('password') or ''
        role     = request.POST.get('role') or 'ADMIN'  # ADMIN | DENTISTA | PACIENTE

        user = auth.authenticate(request, username=username, password=password)
        if user:
            auth.login(request, user)
            # Redirecciones sugeridas por rol (ajusta a tus nombres reales)
            if role == 'ADMIN':
                return redirect('/dentista/')  # o nombre de url
            if role == 'DENTISTA':
                return redirect('/dentista/agenda/')  # o nombre de url
            return redirect('/paciente/')  # PACIENTE
        messages.error(request, 'Usuario o contraseña inválidos.')
    return render(request, 'accounts/login.html')
