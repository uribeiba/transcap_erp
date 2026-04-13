from django.contrib import admin
from .models import Ciudad, EstadoFacturacionGuia
from centro_comercio.models import Cliente   # ← importación correcta


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "rut", "activo")   # ← campo corregido
    list_filter = ("activo",)
    search_fields = ("razon_social", "rut")            # ← campo corregido


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
    search_fields = ("nro_guia", "nro_factura", "referencia_viaje", "cliente__razon_social")  # ← también ajustado
    readonly_fields = ("creado_el", "actualizado_el")
    date_hierarchy = "fecha"