from django.urls import path
from . import views

app_name = "documentos"

urlpatterns = [

    path(
        "",
        views.dashboard_documentos,
        name="dashboard"
    ),

    path(
        "crear/",
        views.crear_documento,
        name="crear"
    ),

    path(
        "lista/",
        views.lista_documentos,
        name="lista"
    ),

    path(
        "eliminar/<int:pk>/",
        views.eliminar_documento,
        name="eliminar"
    ),

]