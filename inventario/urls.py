from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    # Dashboard
    path("dashboard/", views.dashboard_inventario, name="dashboard"),

    # Productos
    path("productos/", views.lista_productos, name="lista_productos"),
    path("productos/nuevo/", views.crear_producto, name="crear_producto"),
    path(
        "productos/<int:pk>/editar/",
        views.editar_producto,
        name="editar_producto",
    ),
    path(
        "productos/<int:pk>/kardex/",
        views.kardex_producto,
        name="kardex_producto",
    ),
    path(
        "productos/<int:pk>/kardex/print/",
        views.kardex_producto_print,
        name="kardex_producto_print",
    ),

    # Movimientos
    path("movimientos/", views.lista_movimientos, name="lista_movimientos"),
    path(
        "movimientos/nuevo/",
        views.registrar_movimiento,
        name="registrar_movimiento",
    ),

    # Categorías
    path("categorias/", views.lista_categorias, name="lista_categorias"),
    path(
        "categorias/nueva/",
        views.crear_categoria,
        name="crear_categoria",
    ),
    path(
        "categorias/<int:pk>/editar/",
        views.editar_categoria,
        name="editar_categoria",
    ),
    path(
        "categorias/<int:pk>/eliminar/",
        views.eliminar_categoria,
        name="eliminar_categoria",
    ),
    
    
]
