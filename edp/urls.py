from django.urls import path
from . import views

app_name = "edp"

urlpatterns = [
    path("", views.edp_panel, name="panel"),
    
    # Wizard
    path("nuevo/", views.edp_wizard_new, name="wizard_new"),
    path("<int:edp_id>/wizard/<str:step>/", views.edp_wizard, name="wizard"),
    
    # PDF (DEBE IR ANTES de detalle)
    path("<int:edp_id>/pdf/", views.edp_pdf, name="pdf"),
    
    # Acciones extra
    path("<int:edp_id>/detalle/", views.edp_detalle, name="detalle"),
    path("<int:edp_id>/eliminar/", views.edp_eliminar, name="eliminar"),
]