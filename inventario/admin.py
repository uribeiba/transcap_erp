from django.contrib import admin
from .models import (
    CategoriaProducto,
    Bodega,
    Producto,
    Stock,
    MovimientoInventario,
)


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ubicacion", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "ubicacion")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "categoria",
        "unidad_medida",
        "stock_minimo",
        "activo",
    )
    list_filter = ("categoria", "unidad_medida", "activo")
    search_fields = ("codigo", "nombre")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("producto", "bodega", "cantidad")
    # uso la versión más completa que ya tenías
    list_filter = ("bodega", "producto__categoria")
    search_fields = (
        "producto__codigo",
        "producto__nombre",
        "bodega__nombre",
    )


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "tipo",
        "producto",
        "bodega",
        "cantidad",
        "usuario_registro",
    )
    # combino lo mejor de ambas versiones
    list_filter = ("tipo", "bodega", "producto", "producto__categoria")
    search_fields = (
        "producto__codigo",
        "producto__nombre",
        "referencia",
        "observacion",
    )
    readonly_fields = ("fecha",)
    date_hierarchy = "fecha"
