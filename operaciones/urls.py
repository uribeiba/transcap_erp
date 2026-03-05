from django.urls import path
from . import views
from . import views_estatus

app_name = "operaciones"

urlpatterns = [

    # =====================================================
    # TABLERO OPERACIONES
    # =====================================================
    path("tablero/", views.tablero_diario, name="tablero_diario"),
    path("tablero/refresh/", views.tablero_refresh, name="tablero_refresh"),

    # =====================================================
    # CREACIÓN RÁPIDA
    # =====================================================
    path("crear/", views.crear_rapido, name="crear_rapido"),

    # =====================================================
    # REGISTROS (edición multiusuario)
    # =====================================================
    path("registro/<int:pk>/detalle/", views.registro_detalle_json, name="registro_detalle_json"),
    path("registro/<int:pk>/lock/", views.registro_lock, name="registro_lock"),
    path("registro/<int:pk>/unlock/", views.registro_unlock, name="registro_unlock"),
    path("registro/<int:pk>/guardar/", views.registro_guardar, name="registro_guardar"),
    path("registro/<int:pk>/heartbeat/", views.registro_heartbeat, name="registro_heartbeat"),

    # =====================================================
    # PRESENCIA MULTIUSUARIO
    # =====================================================
    path("presencia/ping/", views.presencia_ping, name="presencia_ping"),
    path("presencia/lista/", views.presencia_lista, name="presencia_lista"),

    # =====================================================
    # ESTATUS DE VIAJES (AM / PM)
    # =====================================================
    path("estatus-viajes/", views.estatus_viajes_panel, name="estatus_viajes_panel"),
    path("estatus-viajes/guardar/", views.estatus_viajes_guardar, name="estatus_viajes_guardar"),
    path("estatus-viajes/<int:pk>/eliminar/", views.estatus_viajes_eliminar, name="estatus_viajes_eliminar"),
    path("estatus-viajes/copiar-am-pm/", views.estatus_viajes_copiar_am_a_pm, name="estatus_viajes_copiar_am_a_pm"),
    path("estatus-viajes/export/xlsx/", views.estatus_viajes_export_xlsx, name="estatus_viajes_export_xlsx"),

    # =====================================================
    # ESTATUS DE VIAJES — PLANILLA (MODO PRO+)
    # =====================================================
    path("estatus-viajes/planilla/", views_estatus.estatus_viajes_planilla, name="estatus_viajes_planilla"),
    path(
        "estatus-viajes/export/planilla/xlsx/",
        views_estatus.estatus_viajes_export_planilla_xlsx,
        name="estatus_viajes_export_planilla_xlsx",
    ),
]