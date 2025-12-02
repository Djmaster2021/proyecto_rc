# domain/urls.py
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "domain"

urlpatterns = [
    path("", getattr(views, "index", TemplateView.as_view(template_name="domain/index.html")), name="index"),
]
