# remuneraciones/models/parametros.py
from django.db import models
from decimal import Decimal

class ParametroGeneral(models.Model):
    """
    Parámetros generales del sistema de remuneraciones
    """
    TIPO_CHOICES = [
        ('TOPE_AFP', 'Tope Imponible AFP'),
        ('TOPE_SALUD', 'Tope Imponible Salud'),
        ('UTM', 'Valor UTM'),
        ('UF', 'Valor UF'),
        ('IPC', 'IPC Acumulado'),
        ('Sueldo_Minimo', 'Sueldo Mínimo Mensual'),
        ('Gratificacion_Legal', 'Porcentaje Gratificación Legal'),
        ('AFC', 'Porcentaje AFC'),
    ]
    
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, unique=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor numérico o porcentaje")
    fecha_vigencia = models.DateField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Parámetro General"
        verbose_name_plural = "Parámetros Generales"
        ordering = ['tipo', '-fecha_vigencia']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.valor}"


class AsignacionFamiliar(models.Model):
    """
    Tabla de Asignación Familiar por carga
    """
    CARGA_CHOICES = [
        ('HIJO', 'Hijo(a)'),
        ('CONYUGE', 'Cónyuge'),
        ('MADRE', 'Madre'),
        ('PADRE', 'Padre'),
    ]
    
    tipo_carga = models.CharField(max_length=20, choices=CARGA_CHOICES)
    desde_sueldo = models.DecimalField(max_digits=12, decimal_places=0)
    hasta_sueldo = models.DecimalField(max_digits=12, decimal_places=0)
    monto_asignacion = models.DecimalField(max_digits=10, decimal_places=0)
    vigencia = models.DateField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Asignación Familiar"
        verbose_name_plural = "Asignaciones Familiares"
    
    def __str__(self):
        return f"{self.tipo_carga}: ${self.monto_asignacion:,.0f}"