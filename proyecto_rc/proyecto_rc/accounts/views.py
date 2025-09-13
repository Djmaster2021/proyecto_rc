from django.shortcuts import render, redirect

def login_view(request):
    return render(request, "accounts/login.html")

def register_view(request):
    return render(request, "accounts/register.html")

def logout_view(request):
    # placeholder: más adelante implementarás logout real
    return redirect("home")
