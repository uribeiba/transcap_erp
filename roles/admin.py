from django.contrib import admin
from .models import Rol, UsuarioRol

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'creado_el')
    filter_horizontal = ('permisos',)
    search_fields = ('nombre',)

@admin.register(UsuarioRol)
class UsuarioRolAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol')
    search_fields = ('usuario__username', 'usuario__email', 'rol__nombre')