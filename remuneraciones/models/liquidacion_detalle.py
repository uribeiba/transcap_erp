# remuneraciones/models/liquidacion_detalle.py
from django.db import models

class LiquidacionDetalle(models.Model):
    liquidacion = models.ForeignKey('Liquidacion', on_delete=models.CASCADE, related_name='detalles')
    concepto = models.ForeignKey('Concepto', on_delete=models.CASCADE)

    monto = models.DecimalField(max_digits=12, decimal_places=0)

    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    def __str__(self):
        return f"{self.concepto} - {self.monto}"