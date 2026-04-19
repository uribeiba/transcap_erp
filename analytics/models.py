from django.db import models
from django.utils import timezone
from taller.models import Vehiculo, Conductor
from operaciones.models import EstatusOperacionalViaje

class GastoCombustible(models.Model):
    """Registro manual de carga de combustible"""
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='gastos_combustible')
    conductor = models.ForeignKey(Conductor, on_delete=models.SET_NULL, null=True, blank=True)
    viaje = models.ForeignKey(EstatusOperacionalViaje, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha = models.DateField(default=timezone.now)
    litros = models.DecimalField(max_digits=10, decimal_places=2)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    kilometraje = models.PositiveIntegerField(help_text="Kilometraje al momento de la carga")
    observacion = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Gasto Combustible'
        verbose_name_plural = 'Gastos Combustible'
    
    def __str__(self):
        return f"{self.vehiculo.patente} - {self.litros}L - ${self.monto}"


class GastoPeaje(models.Model):
    """Registro manual de peajes"""
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='gastos_peaje')
    conductor = models.ForeignKey(Conductor, on_delete=models.SET_NULL, null=True, blank=True)
    viaje = models.ForeignKey(EstatusOperacionalViaje, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha = models.DateField(default=timezone.now)
    ruta = models.CharField(max_length=200, help_text="Ej: Ruta 5, tramo Los Vilos - La Serena")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    observacion = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Gasto Peaje'
        verbose_name_plural = 'Gastos Peaje'
    
    def __str__(self):
        return f"{self.vehiculo.patente} - {self.ruta} - ${self.monto}"


class CostoViaje(models.Model):
    """Resumen de costos por viaje (para estadísticas)"""
    viaje = models.OneToOneField(EstatusOperacionalViaje, on_delete=models.CASCADE, related_name='costo_analytics')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE)
    
    km_recorridos = models.PositiveIntegerField(help_text="Kilómetros recorridos en el viaje")
    total_combustible = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_peajes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_mantencion = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    fecha = models.DateField(default=timezone.now)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Costo por Viaje'
        verbose_name_plural = 'Costos por Viaje'
    
    def calcular_costo_total(self):
        self.costo_total = self.total_combustible + self.total_peajes + self.total_mantencion
        return self.costo_total
    
    def __str__(self):
        return f"Viaje {self.viaje.id} - {self.vehiculo.patente} - ${self.costo_total}"