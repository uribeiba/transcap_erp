from django.urls import path
from . import views

app_name = "bitacora"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("nuevo/", views.crear, name="crear"),
    path("editar/<int:pk>/", views.editar, name="editar"),
    path("detalle/<int:pk>/", views.detalle, name="detalle"),
    path("eliminar/<int:pk>/", views.eliminar, name="eliminar"),
    path('reporte-guias/', views.reporte_guias, name='reporte_guias'),

    path(
        "api/coordinacion/<int:id>/",
        views.api_coordinacion_detalle,
        name="api_coordinacion_detalle",
    ),
    path("api/clientes/", views.api_clientes, name="api_clientes"),
]