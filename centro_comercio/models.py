from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


rut_validator = RegexValidator(
    regex=r"^\d{7,8}-[\dkK]$",
    message="RUT inválido. Formato esperado: 12345678-9"
)

class Cliente(models.Model):
    rut = models.CharField("RUT", max_length=12, unique=True, validators=[rut_validator])
    razon_social = models.CharField("Razón social", max_length=255)
    giro = models.CharField("Giro", max_length=255, blank=True, default="")
    telefono = models.CharField("Teléfono", max_length=50, blank=True, default="")
    email = models.EmailField("E-mail", blank=True, default="")
    direccion = models.CharField("Dirección", max_length=255, blank=True, default="")
    localidad = models.CharField("Localidad", max_length=120, blank=True, default="")
    activo = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["razon_social"]

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"



class CotizacionEstado(models.TextChoices):
    PENDIENTE = "PEND", "Pendiente"
    ACEPTADA  = "ACEP", "Aceptada"
    ANULADA   = "ANUL", "Anulada"


class Cotizacion(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey("Cliente", on_delete=models.PROTECT, related_name="cotizaciones")

    fecha = models.DateField(default=timezone.localdate)
    vigencia_hasta = models.DateField(default=timezone.localdate)

    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    terminos = models.TextField(blank=True, default="")

    estado = models.CharField(max_length=4, choices=CotizacionEstado.choices, default=CotizacionEstado.PENDIENTE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.codigo} - {self.cliente}"

    @staticmethod
    def siguiente_codigo():
        # COT-0001...
        last = Cotizacion.objects.order_by("-id").first()
        if not last:
            return "COT-0001"
        # intenta extraer correlativo
        import re
        m = re.search(r"(\d+)$", last.codigo or "")
        n = int(m.group(1)) + 1 if m else (last.id + 1)
        return f"COT-{n:04d}"

    @property
    def total_items(self):
        return sum((it.total for it in self.items.all()), 0)

    @property
    def total_neto(self):
        return max(self.total_items - (self.descuento or 0), 0)


class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name="items")
    titulo = models.CharField(max_length=200)
    unidad = models.CharField(max_length=50, blank=True, default="")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    exento = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    @property
    def total(self):
        try:
            return (self.cantidad or 0) * (self.valor_unitario or 0)
        except Exception:
            return 0
 
 
 
 
 