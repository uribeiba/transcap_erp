# remuneraciones/models/liquidacion.py
from django.db import models
from decimal import Decimal

class Liquidacion(models.Model):
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='liquidaciones')
    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE, related_name='liquidaciones')
    periodo = models.CharField(max_length=7, help_text="Formato YYYY-MM", db_index=True) # EJ: 2026-04
    
    total_haberes = models.DecimalField(max_digits=12, decimal_places=0)
    total_descuentos = models.DecimalField(max_digits=12, decimal_places=0)
    liquido_pagar = models.DecimalField(max_digits=12, decimal_places=0)
    
    fecha_pago = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['contrato', 'periodo'] # Evita duplicados
        ordering = ['-periodo', 'contrato__empleado__apellidos']

    def __str__(self):
        return f"Liquidación {self.periodo} - {self.empleado.nombre_completo}"