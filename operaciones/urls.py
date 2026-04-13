from django.urls import path
from . import views_estatus

app_name = "operaciones"

urlpatterns = [
    # Estatus de viajes PRO
    path("estatus-viajes/", views_estatus.estatus_viajes_panel, name="estatus_viajes_panel"),
    path("estatus-viajes/guardar/", views_estatus.estatus_viajes_guardar, name="estatus_viajes_guardar"),
    path("estatus-viajes/<int:pk>/eliminar/", views_estatus.estatus_viajes_eliminar, name="estatus_viajes_eliminar"),
    path("estatus-viajes/<int:pk>/a-bitacora/", views_estatus.estatus_viajes_a_bitacora, name="estatus_viajes_a_bitacora"),
    path("estatus-viajes/copiar-am-pm/", views_estatus.estatus_viajes_copiar_am_a_pm, name="estatus_viajes_copiar_am_a_pm"),
    path("estatus-viajes/export/xlsx/", views_estatus.estatus_viajes_export_xlsx, name="estatus_viajes_export_xlsx"),

    # Planilla
    path("estatus-viajes/planilla/", views_estatus.estatus_viajes_planilla, name="estatus_viajes_planilla"),
    path(
        "estatus-viajes/export/planilla/xlsx/",
        views_estatus.estatus_viajes_export_planilla_xlsx,
        name="estatus_viajes_export_planilla_xlsx",
    ),
]