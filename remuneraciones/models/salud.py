# remuneraciones/models/salud.py
from django.db import models

class Salud(models.Model):
    TIPO_CHOICES = [
        ('FONASA', 'Fonasa'),
        ('ISAPRE', 'Isapre'),
        ('OTRO', 'Otro Sistema'),
    ]
    
    PLAN_CHOICES = [
        ('BASE', 'Plan Base 7%'),
        ('COMPLEMENTARIO', 'Plan Complementario'),
        ('PREMIUM', 'Plan Premium'),
    ]
    
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True, blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='BASE')
    
    tasa_cotizacion = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.07,
        help_text="Ej: 0.07 = 7%"
    )
    
    tasa_adicional = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text="Para planes complementarios"
    )
    
    monto_adicional = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        help_text="Monto fijo adicional si aplica"
    )
    
    fecha_vigencia = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Salud"
        verbose_name_plural = "Salud (Fonasa/Isapre)"
        ordering = ['tipo', 'nombre']
    
    def tasa_total(self):
        return self.tasa_cotizacion + self.tasa_adicional
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()}) - {self.tasa_total()*100:.1f}%"