# remuneraciones/models/tablas.py

from django.db import models
from decimal import Decimal


class TramoImpuesto(models.Model):
    """
    Tabla de impuesto único SII (en UTM)
    """

    desde = models.DecimalField(max_digits=10, decimal_places=2)
    hasta = models.DecimalField(max_digits=10, decimal_places=2)

    factor = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Factor multiplicador"
    )

    rebaja = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Rebaja en UTM"
    )

    def __str__(self):
        return f"{self.desde} - {self.hasta} UTM"