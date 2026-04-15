from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    permisos = models.ManyToManyField(Permission, blank=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class UsuarioRol(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rol_usuario')
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Usuario Rol"
        verbose_name_plural = "Usuarios Roles"

    def __str__(self):
        return f"{self.usuario.username} - {self.rol.nombre}"


# ============================================================
# PERMISOS PERSONALIZADOS PARA MÓDULOS
# ============================================================

def crear_permisos_personalizados():
    """Función para crear permisos personalizados (ejecutar una vez)"""
    content_type = ContentType.objects.get_for_model(User)
    
    permisos_menu = [
        ('puede_ver_dashboard', 'Puede ver el Panel de Control'),
        ('puede_ver_finanzas', 'Puede ver el módulo Finanzas'),
        ('puede_ver_compras', 'Puede ver el módulo Compras'),
        ('puede_ver_inventario', 'Puede ver el módulo Inventario'),
        ('puede_ver_taller', 'Puede ver el módulo Taller/Flota'),
        ('puede_ver_rrhh', 'Puede ver el módulo RRHH/Remuneraciones'),
        ('puede_ver_facturacion', 'Puede ver el módulo Facturación'),
        ('puede_ver_gastos', 'Puede ver el módulo Gastos'),
        ('puede_ver_bitacora', 'Puede ver el módulo Bitácora'),
        ('puede_ver_edp', 'Puede ver el módulo EDP'),
        ('puede_ver_operaciones', 'Puede ver el módulo Operaciones'),
        ('puede_ver_clientes', 'Puede ver el módulo Clientes'),
        ('puede_ver_cotizaciones', 'Puede ver el módulo Cotizaciones'),
        ('puede_ver_parametros', 'Puede ver el módulo Parámetros'),
        ('puede_ver_financiero', 'Puede ver datos financieros (montos)'),
        ('puede_ver_roles', 'Puede gestionar roles y permisos'),
    ]
    
    creados = []
    for codename, name in permisos_menu:
        perm, created = Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type,
        )
        creados.append((codename, created))
    
    return creados