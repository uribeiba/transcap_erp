# config/edp/models.py
from django.db import models
from django.utils import timezone
from servicios.models import Servicio  # ✅ Ya está correcto
import re

class EDP(models.Model):
    ESTADOS = (
        ("BORR", "Borrador"),
        ("PROC", "En proceso"),
        ("PAGA", "Pagado"),
        ("ANUL", "Anulado"),
    )

    codigo = models.CharField(max_length=20, unique=True)
    fecha_pago = models.DateField(default=timezone.now)
    glosa = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=4, choices=ESTADOS, default="BORR")

    neto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.codigo

    @staticmethod
    def generar_codigo():
        """Genera código secuencial: EDP_0994, EDP_0995, etc."""
        from django.db.models import Max
        
        # Buscar el último código numérico
        ultimo_edp = EDP.objects.filter(codigo__regex=r'^EDP_\d+$').order_by('-id').first()
        
        if not ultimo_edp:
            return "EDP_0001"
        
        # Extraer el número del último código
        match = re.search(r'EDP_(\d+)', ultimo_edp.codigo)
        if match:
            siguiente_num = int(match.group(1)) + 1
        else:
            siguiente_num = EDP.objects.count() + 1
        
        # Formatear con ceros a la izquierda
        return f"EDP_{siguiente_num:04d}"

    def save(self, *args, **kwargs):
        # Si no tiene código, generarlo
        if not self.codigo:
            self.codigo = self.generar_codigo()
        super().save(*args, **kwargs)

    def recalcular_totales(self, iva_rate=0.19):
        lineas = self.items.all()
        neto = sum((float(l.total_linea) for l in lineas), 0)
        iva = round(float(neto) * iva_rate, 2)
        total = round(float(neto) + iva, 2)

        self.neto = neto
        self.iva = iva
        self.total = total
        self.save(update_fields=["neto", "iva", "total"])


class EDPServicio(models.Model):
    edp = models.ForeignKey(EDP, related_name="items", on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)

    tarifa = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estadia = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_linea = (self.tarifa or 0) + (self.estadia or 0)
        super().save(*args, **kwargs)


class EDPago(models.Model):
    MEDIOS = (
        ("EFEC", "Efectivo"),
        ("TRAN", "Transferencia"),
        ("TARJ", "Tarjeta"),
        ("OTRO", "Otro"),
    )

    edp = models.ForeignKey(EDP, related_name="pagos", on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    medio_pago = models.CharField(max_length=4, choices=MEDIOS, default="TRAN")
    monto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    referencia = models.CharField(max_length=120, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)