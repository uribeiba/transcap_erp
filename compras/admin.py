from django.contrib import admin
from .models import Proveedor, OrdenCompra, DetalleOrdenCompra

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'rut', 'telefono', 'activo')
    search_fields = ('razon_social', 'rut')

class DetalleInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 1

@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fecha', 'proveedor', 'estado', 'total')
    list_filter = ('estado', 'fecha')
    inlines = [DetalleInline]