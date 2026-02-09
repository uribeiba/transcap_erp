# config/edp/urls.py
from django.urls import path
from . import views

app_name = "edp"

urlpatterns = [
    path("", views.edp_panel, name="panel"),  # Cambiado de views.panel a views.edp_panel

    # Wizard
    path("nuevo/", views.edp_wizard_new, name="wizard_new"),
    path("<int:edp_id>/wizard/<str:step>/", views.edp_wizard, name="wizard"),

    # Acciones extra
    path("<int:edp_id>/detalle/", views.edp_detalle, name="detalle"),
    path("<int:edp_id>/eliminar/", views.edp_eliminar, name="eliminar"),
]