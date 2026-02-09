from django.db import models
from django.utils import timezone
from centro_comercio.models import Cotizacion

class Servicio(models.Model):
    ESTADOS_SERVICIO = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]

    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código Servicio")
    cotizacion = models.ForeignKey(
        Cotizacion, 
        on_delete=models.PROTECT, 
        related_name='servicios',
        verbose_name="Cotización"
    )
    fecha_inicio = models.DateField(default=timezone.localdate, verbose_name="Inicio Servicio")
    fecha_termino = models.DateField(default=timezone.localdate, verbose_name="Término Servicio")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_SERVICIO, 
        default='PENDIENTE',
        verbose_name="Estado del Servicio"
    )
    notas_internas = models.TextField(blank=True, verbose_name="Notas Internas")
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_inicio', '-creado_en']
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return f"{self.codigo} - {self.cotizacion.cliente.razon_social}"

    def cliente(self):
        return self.cotizacion.cliente

    @staticmethod
    def siguiente_codigo():
        """Genera código secuencial: SERV-1012, SERV-1013, etc."""
        from django.db.models import Max
        import re
        
        ultimo = Servicio.objects.aggregate(Max('id'))['id__max']
        if not ultimo:
            return "SERV-1001"
        
        # Buscar el último código numérico
        ultimo_servicio = Servicio.objects.order_by('-id').first()
        if ultimo_servicio and ultimo_servicio.codigo:
            match = re.search(r'(\d+)$', ultimo_servicio.codigo)
            if match:
                siguiente_num = int(match.group(1)) + 1
            else:
                siguiente_num = ultimo + 1001
        else:
            siguiente_num = ultimo + 1001
        
        return f"SERV-{siguiente_num}"

    def duracion_dias(self):
        """Calcula la duración en días del servicio."""
        if self.fecha_inicio and self.fecha_termino:
            return (self.fecha_termino - self.fecha_inicio).days
        return 0