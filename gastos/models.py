from django.db import models
from django.utils import timezone
from decimal import Decimal

class CategoriaGasto(models.Model):
    TIPO_CHOICES = [
        ('OPER', 'Operacional'),
        ('ADMIN', 'Administrativo'),
        ('FIN', 'Financiero'),
    ]
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=5, choices=TIPO_CHOICES, default='OPER')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría de Gasto"
        verbose_name_plural = "Categorías de Gastos"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Gasto(models.Model):
    FORMA_PAGO_CHOICES = [
        ('EF', 'Efectivo'),
        ('TR', 'Transferencia'),
        ('CH', 'Cheque'),
        ('TC', 'Tarjeta Crédito'),
    ]
    fecha = models.DateField(default=timezone.localdate)
    categoria = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT)
    proveedor = models.CharField(max_length=200, blank=True, help_text="Nombre del proveedor o razón social")
    descripcion = models.CharField(max_length=255)
    monto_neto = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    documento = models.CharField(max_length=30, blank=True, help_text="Factura, Boleta, etc.")
    nro_documento = models.CharField(max_length=50, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    forma_pago = models.CharField(max_length=2, choices=FORMA_PAGO_CHOICES, blank=True)
    observaciones = models.TextField(blank=True)
    # Opcional: asociar a un vehículo o bitácora
    vehiculo = models.ForeignKey('taller.Vehiculo', on_delete=models.SET_NULL, null=True, blank=True)
    bitacora = models.ForeignKey('bitacora.Bitacora', on_delete=models.SET_NULL, null=True, blank=True)

    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-id']

    def save(self, *args, **kwargs):
        self.monto_total = self.monto_neto + self.iva
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fecha} - {self.categoria.nombre} - ${self.monto_total}"


class GastoRecurrente(models.Model):
    PERIODICIDAD_CHOICES = [
        ('MENSUAL', 'Mensual'),
        ('BIMESTRAL', 'Bimestral'),
        ('TRIMESTRAL', 'Trimestral'),
    ]
    categoria = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT)
    proveedor = models.CharField(max_length=200, blank=True)
    descripcion = models.CharField(max_length=255)
    monto_neto = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    periodicidad = models.CharField(max_length=10, choices=PERIODICIDAD_CHOICES, default='MENSUAL')
    dia_pago = models.IntegerField(help_text="Día del mes (1-31) o -1 para último día")
    activo = models.BooleanField(default=True)
    ultima_generacion = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.descripcion} ({self.get_periodicidad_display()})"