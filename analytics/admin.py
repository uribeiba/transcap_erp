from django.contrib import admin
from .models import GastoCombustible, GastoPeaje, CostoViaje

@admin.register(GastoCombustible)
class GastoCombustibleAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'vehiculo', 'litros', 'monto', 'kilometraje']
    list_filter = ['vehiculo', 'fecha']
    search_fields = ['vehiculo__patente', 'conductor__nombres']

@admin.register(GastoPeaje)
class GastoPeajeAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'vehiculo', 'ruta', 'monto']
    list_filter = ['vehiculo', 'fecha']
    search_fields = ['vehiculo__patente', 'ruta']

@admin.register(CostoViaje)
class CostoViajeAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'vehiculo', 'conductor', 'km_recorridos', 'costo_total']
    list_filter = ['vehiculo', 'fecha']
    search_fields = ['vehiculo__patente', 'conductor__nombres']