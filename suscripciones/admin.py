from django.contrib import admin
from .models import Plan, Suscripcion

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("nombre", "max_usuarios", "activo", "precio_mensual", "precio_anual")
    list_filter = ("activo",)
    search_fields = ("nombre",)

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ("empresa", "plan", "estado", "inicio", "fin", "limite_usuarios")
    list_filter = ("estado", "plan")
    search_fields = ("empresa__razon_social", "empresa__rut", "plan__nombre")
