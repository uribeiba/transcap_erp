from django.contrib import admin
from .models import Cliente, Ciudad, EstadoFacturacionGuia


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "rut")


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(EstadoFacturacionGuia)
class EstadoFacturacionGuiaAdmin(admin.ModelAdmin):
    list_display = (
        "fecha", "correlativo_diario", "cliente", "origen", "destino",
        "nro_guia", "nro_factura", "monto", "estado", "prioridad",
        "bloqueado_por", "bloqueado_desde",
    )
    list_filter = ("fecha", "estado", "prioridad", "origen", "destino")
    search_fields = ("nro_guia", "nro_factura", "referencia_viaje", "cliente__nombre")
    readonly_fields = ("creado_el", "actualizado_el")
    date_hierarchy = "fecha"
