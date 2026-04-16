from django.db import models
from django.utils import timezone
from operaciones.models import EstatusOperacionalViaje
from taller.models import Conductor

class ReporteChofer(models.Model):
    ESTADO_CHOICES = [
        ('PEND', 'Pendiente'),
        ('EN_CAMINO', 'En camino'),
        ('CARGANDO', 'Cargando'),
        ('DESCARGANDO', 'Descargando'),
        ('RETORNO', 'Retorno'),
        ('COMPLETADO', 'Completado'),
    ]
    
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE, related_name='reportes')
    estatus_viaje = models.ForeignKey(EstatusOperacionalViaje, on_delete=models.CASCADE, null=True, blank=True)
    
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PEND')
    ubicacion = models.CharField(max_length=255, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    # Datos de carga/descarga
    lugar_carga = models.CharField(max_length=255, blank=True)
    lugar_descarga = models.CharField(max_length=255, blank=True)
    nro_guia = models.CharField(max_length=50, blank=True)
    oc_edp = models.CharField(max_length=50, blank=True)
    
    creado_el = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.conductor} - {self.fecha} - {self.estado}"

class FotoReporte(models.Model):
    reporte = models.ForeignKey(ReporteChofer, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='reportes_chofer/%Y/%m/%d/')
    descripcion = models.CharField(max_length=255, blank=True)
    creado_el = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Foto {self.id} - {self.reporte.conductor}"
    
class UbicacionChofer(models.Model):
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE, related_name='ubicaciones')
    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)
    velocidad = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Ubicación de Chofer"
        verbose_name_plural = "Ubicaciones de Choferes"
    
    def __str__(self):
        return f"{self.conductor} - {self.timestamp}"