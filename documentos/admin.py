from django.contrib import admin
from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "usuario",
        "tipo_documento",
        "numero_documento",
        "fecha_registro",
        "estado",
    )

    list_filter = (
        "tipo_documento",
        "estado",
        "fecha_registro",
    )

    search_fields = (
        "numero_documento",
        "usuario__username",
    )

    readonly_fields = (
        "fecha_registro",
    )