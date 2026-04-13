# remuneraciones/models/concepto.py
from django.db import models

class Concepto(models.Model):
    TIPO = [
        ('HABER_IMPONIBLE', 'Haber Imponible'),
        ('HABER_NO_IMPONIBLE', 'Haber No Imponible'),
        ('DESCUENTO_LEGAL', 'Descuento Legal'),
        ('DESCUENTO_VOLUNTARIO', 'Descuento Voluntario'),
        ('APORTE_EMPLEADOR', 'Aporte Empleador'),
    ]
    
    CATEGORIA_CHOICES = [
        ('REMUNERACION', 'Remuneración Base'),
        ('HORAS_EXTRA', 'Horas Extra'),
        ('BONOS', 'Bonos'),
        ('MOVILIZACION', 'Movilización'),
        ('COLACION', 'Colación'),
        ('ASIGNACION', 'Asignación Familiar'),
        ('GRATIFICACION', 'Gratificación'),
        ('DESCUENTO', 'Descuentos Varios'),
        ('PRESTAMO', 'Préstamos'),
        ('CAJA_COMPENSACION', 'Caja de Compensación'),
        ('COOPERATIVA', 'Cooperativa'),
    ]
    
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=30, choices=TIPO)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, blank=True, null=True)
    
    es_imponible = models.BooleanField(default=True)
    es_tributable = models.BooleanField(default=True)
    es_afecto_a_descuentos = models.BooleanField(default=True)
    
    formula = models.TextField(blank=True, null=True, help_text="Ej: sueldo_base * 0.25")
    monto_fijo = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    
    orden = models.IntegerField(default=0, help_text="Orden de visualización")
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['orden', 'nombre']
    
    def calcular_monto(self, sueldo_base=0, otras_variables=None):
        """Calcula el monto del concepto según su fórmula o valores fijos"""
        if self.monto_fijo:
            return self.monto_fijo
        if self.porcentaje:
            return sueldo_base * self.porcentaje
        return 0
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()}"