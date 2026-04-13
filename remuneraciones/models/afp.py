# remuneraciones/models/afp.py
from django.db import models
from decimal import Decimal

class AFP(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True, help_text="Código SII de la AFP")
    
    tasa_cotizacion = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Ej: 0.1044 = 10.44%"
    )
    
    comision = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Ej: 0.0069 = 0.69%"
    )
    
    comision_adicional = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text="Comisión adicional si aplica"
    )
    
    seguro_invalidez = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.0144,
        help_text="Seguro de invalidez y sobrevivencia (1.44%)"
    )
    
    fecha_vigencia = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
    
    def tasa_total(self):
        """Retorna la suma de cotización + comisiones"""
        return Decimal(str(self.tasa_cotizacion)) + Decimal(str(self.comision)) + Decimal(str(self.comision_adicional))
    
    def tasa_total_con_seguro(self):
        """Retorna tasa total incluyendo seguro"""
        return self.tasa_total() + Decimal(str(self.seguro_invalidez))
    
    def __str__(self):
        return f"{self.nombre} - {self.tasa_total()*100:.2f}%"