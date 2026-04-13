# remuneraciones/models/empleado.py
from django.db import models

class Empleado(models.Model):
    TIPO_CONTRATO = [
        ('INDEFINIDO', 'Indefinido'),
        ('PLAZO_FIJO', 'Plazo fijo'),
        ('HONORARIOS', 'Honorarios'),
    ]

    rut = models.CharField(max_length=12, unique=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)

    fecha_nacimiento = models.DateField()
    fecha_ingreso = models.DateField()

    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO)

    cargo = models.CharField(max_length=100)
    area = models.CharField(max_length=100, blank=True, null=True)

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.rut} - {self.nombres} {self.apellidos}"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del empleado"""
        return f"{self.nombres} {self.apellidos}"