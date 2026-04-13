# remuneraciones/models/contrato.py
from django.db import models

class Contrato(models.Model):
    TIPO_JORNADA_CHOICES = [
        ('COMPLETA', 'Jornada Completa (45 hrs)'),
        ('PARCIAL', 'Jornada Parcial'),
        ('ART_22', 'Artículo 22 (sin jornada máxima)'),
    ]
    
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='contratos')
    
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=0)
    
    tipo_jornada = models.CharField(max_length=20, choices=TIPO_JORNADA_CHOICES)
    horas_semanales = models.IntegerField(default=45)
    
    # Relaciones ForeignKey (no CharField)
    afp = models.ForeignKey('AFP', on_delete=models.SET_NULL, null=True, related_name='contratos')
    salud = models.ForeignKey('Salud', on_delete=models.SET_NULL, null=True, related_name='contratos')
    
    es_articulo_22 = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Contrato {self.empleado.rut} - {self.fecha_inicio}"