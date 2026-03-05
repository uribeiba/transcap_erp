from django.urls import path
from . import views

app_name = "centro_comercio"

urlpatterns = [
    path("", views.centro_home, name="home"),

    # =========================
    # CLIENTES
    # =========================
    path("clientes/", views.clientes_panel, name="clientes_panel"),
    path("clientes/lista/", views.clientes_lista, name="clientes_lista"),
    path("clientes/nuevo/", views.cliente_form, name="cliente_nuevo"),
    path("clientes/<int:pk>/", views.cliente_detalle, name="cliente_detalle"),
    path("clientes/<int:pk>/editar/", views.cliente_form, name="cliente_editar"),
    path("clientes/<int:pk>/eliminar/", views.cliente_eliminar, name="cliente_eliminar"),

    # =========================
    # COTIZACIONES
    # =========================
    path("cotizaciones/", views.cotizaciones_panel, name="cotizaciones_panel"),
    path("cotizaciones/lista/", views.cotizaciones_lista, name="cotizaciones_lista"),

    # Crear
    path("cotizaciones/nuevo/", views.cotizacion_form, name="cotizacion_nuevo"),

    # Editar
    path("cotizaciones/<int:pk>/editar/", views.cotizacion_form, name="cotizacion_editar"),

    # Detalle
    path("cotizaciones/<int:pk>/", views.cotizacion_detalle, name="cotizacion_detalle"),

    # Eliminar
    path("cotizaciones/<int:pk>/eliminar/", views.cotizacion_eliminar, name="cotizacion_eliminar"),

    # =========================
    # 🔹 ALIAS PARA TEMPLATE (IMPORTANTE)
    # =========================
    # Permite usar {% url 'centro_comercio:cotizacion_form' %}
    path("cotizaciones/form/", views.cotizacion_form, name="cotizacion_form"),
    path("cotizaciones/<int:pk>/form/", views.cotizacion_form, name="cotizacion_form"),
]
