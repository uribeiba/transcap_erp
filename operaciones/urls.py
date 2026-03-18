from django.urls import path
from . import views
from . import views_estatus

app_name = "operaciones"

urlpatterns = [
    path("tablero/", views.tablero_diario, name="tablero_diario"),
    path("tablero/refresh/", views.tablero_refresh, name="tablero_refresh"),

    path("crear/", views.crear_rapido, name="crear_rapido"),

    path("registro/<int:pk>/detalle/", views.registro_detalle_json, name="registro_detalle_json"),
    path("registro/<int:pk>/lock/", views.registro_lock, name="registro_lock"),
    path("registro/<int:pk>/unlock/", views.registro_unlock, name="registro_unlock"),
    path("registro/<int:pk>/guardar/", views.registro_guardar, name="registro_guardar"),
    path("registro/<int:pk>/heartbeat/", views.registro_heartbeat, name="registro_heartbeat"),

    path("presencia/ping/", views.presencia_ping, name="presencia_ping"),
    path("presencia/lista/", views.presencia_lista, name="presencia_lista"),

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