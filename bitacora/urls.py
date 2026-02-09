from django.urls import path
from . import views

app_name = "bitacora"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("nuevo/", views.crear, name="crear"),
    path(
        "api/coordinacion/<int:id>/",
        views.api_coordinacion_detalle,
        name="api_coordinacion_detalle",
    ),
    path("api/clientes/", views.api_clientes, name="api_clientes"),
]
