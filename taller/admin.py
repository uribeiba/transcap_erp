from django.contrib import admin
from .models import (
    Vehiculo,
    Taller,
    Conductor,
    DocumentoVehiculo,
    DocumentoConductor,
    Mantenimiento,
    MultaConductor,
    RutaViaje,
    CoordinacionViaje,
)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("patente", "marca", "modelo", "tipo", "estado", "activo")
    search_fields = ("patente", "marca", "modelo")
    list_filter = ("tipo", "estado", "activo")


@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ubicacion", "telefono", "activo")
    search_fields = ("nombre", "ubicacion")
    list_filter = ("activo",)


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombres", "apellidos", "activo")
    search_fields = ("rut", "nombres", "apellidos")
    list_filter = ("activo",)


@admin.register(DocumentoVehiculo)
class DocumentoVehiculoAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "tipo", "fecha_vencimiento")
    search_fields = ("vehiculo__patente",)
    list_filter = ("tipo",)


@admin.register(DocumentoConductor)
class DocumentoConductorAdmin(admin.ModelAdmin):
    list_display = ("conductor", "tipo", "fecha_vencimiento")
    search_fields = ("conductor__rut", "conductor__nombres", "conductor__apellidos")
    list_filter = ("tipo",)


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ("vehiculo", "taller", "tipo", "estado",
                    "fecha_programada", "fecha_real")
    search_fields = ("vehiculo__patente", "taller__nombre")
    list_filter = ("tipo", "estado")


@admin.register(MultaConductor)
class MultaConductorAdmin(admin.ModelAdmin):
    list_display = ("conductor", "vehiculo", "fecha", "infraccion", "monto", "estado")
    search_fields = ("conductor__rut", "conductor__nombres", "conductor__apellidos")
    list_filter = ("estado",)


@admin.register(RutaViaje)
class RutaViajeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "origen", "destino", "activo")
    search_fields = ("nombre", "origen", "destino")
    list_filter = ("activo",)


@admin.register(CoordinacionViaje)
class CoordinacionViajeAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_carga",
        "origen",
        "destino",
        "conductor",
        "tracto_camion",
        "semirremolque",
        "estado",
    )
    search_fields = ("origen", "destino", "conductor__nombres", "conductor__apellidos")
    list_filter = ("estado", "ruta")
