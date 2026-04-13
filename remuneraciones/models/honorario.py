# remuneraciones/models/honorario.py
from django.db import models
from decimal import Decimal

class Honorario(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('PAGADO', 'Pagado'),
        ('ANULADO', 'Anulado'),
    ]
    
    rut_beneficiario = models.CharField(max_length=12)
    nombre_beneficiario = models.CharField(max_length=200)
    periodo = models.CharField(max_length=7)
    monto_bruto = models.DecimalField(max_digits=12, decimal_places=0)
    monto_retencion = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    monto_liquido = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='BORRADOR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.monto_bruto:
            self.monto_retencion = self.monto_bruto * Decimal('0.1225')
            self.monto_liquido = self.monto_bruto - self.monto_retencion
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.periodo} - {self.nombre_beneficiario}"