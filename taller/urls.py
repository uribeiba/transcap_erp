from django.urls import path
from . import views

urlpatterns = [
    path("flota/", views.flota_lista, name="taller_flota"),
    path("flota/nuevo/", views.vehiculo_crear, name="taller_vehiculo_nuevo"),
    path("flota/<int:pk>/editar/", views.vehiculo_editar, name="taller_vehiculo_editar"),

    path("conductores/", views.conductores_lista, name="taller_conductores"),
    path("conductores/nuevo/", views.conductor_crear, name="taller_conductor_nuevo"),
    path("conductores/<int:pk>/editar/", views.conductor_editar, name="taller_conductor_editar"),

    # Mantenimientos
    path("mantenimientos/", views.mantenimientos_lista, name="taller_mantenimientos"),
    path("mantenimientos/nuevo/", views.mantenimiento_crear, name="taller_mantenimiento_nuevo"),
    path("mantenimientos/<int:pk>/editar/", views.mantenimiento_editar, name="taller_mantenimiento_editar"),
    path(
        "mantenimientos/<int:pk>/estado/<str:nuevo_estado>/",
        views.mantenimiento_cambiar_estado,
        name="taller_mantenimiento_cambiar_estado",
    ),

    # Documentos (vehículos)
    path("documentos/vehiculos/", views.documentos_vehiculo_lista, name="taller_docs_vehiculos"),
    path("documentos/vehiculos/nuevo/", views.documento_vehiculo_nuevo, name="taller_doc_vehiculo_nuevo"),
    path("documentos/vehiculos/<int:pk>/editar/", views.documento_vehiculo_editar, name="taller_doc_vehiculo_editar"),

    # Documentos (conductores)
    path("documentos/conductores/", views.documentos_conductor_lista, name="taller_docs_conductores"),
    path("documentos/conductores/nuevo/", views.documento_conductor_nuevo, name="taller_doc_conductor_nuevo"),
    path("documentos/conductores/<int:pk>/editar/", views.documento_conductor_editar, name="taller_doc_conductor_editar"),

    # Reportes por vehículo
    path("reportes/vehiculo/", views.reporte_vehiculo_selector, name="taller_reporte_vehiculo_selector"),
    path("reportes/vehiculo/<int:vehiculo_id>/", views.reporte_vehiculo, name="taller_reporte_vehiculo"),
    path("reportes/vehiculo/<int:vehiculo_id>/pdf/", views.reporte_vehiculo_pdf, name="taller_reporte_vehiculo_pdf"),

    # Reportes de conductores
    path("reportes/conductor/", views.reporte_conductor_selector, name="taller_reporte_conductor_selector"),
    path("reportes/conductor/<int:conductor_id>/", views.reporte_conductor, name="taller_reporte_conductor"),
    path("reportes/conductor/<int:conductor_id>/pdf/", views.reporte_conductor_pdf, name="taller_reporte_conductor_pdf"),
    path("ranking/conductores-multas/", views.ranking_conductores_multas, name="taller_ranking_multas"),

    # Debug temporal
    path("debug/vehiculos/", views.debug_vehiculos_tipo, name="taller_debug_vehiculos"),
    
    path("mantenimientos/<int:pk>/repuestos/<int:repuesto_id>/eliminar/",views.mantenimiento_repuesto_eliminar,name="taller_mantenimiento_repuesto_eliminar"),
    path("dashboard/", views.dashboard_taller, name="taller_dashboard"),
]