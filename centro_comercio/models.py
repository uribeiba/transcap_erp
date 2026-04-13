from django.db import models
from django.utils import timezone
from decimal import Decimal
import re
from django.db import models, transaction
from django.core.exceptions import ValidationError


class Cliente(models.Model):
    """Modelo de cliente"""
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social")
    giro = models.CharField(max_length=100, blank=True, verbose_name="Giro")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    direccion = models.CharField(max_length=200, blank=True, verbose_name="Dirección")
    localidad = models.CharField(max_length=100, blank=True, verbose_name="Localidad")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["razon_social"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"


class Vendedor(models.Model):
    """Modelo de vendedor"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(blank=True, verbose_name="Email")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    comision_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Comisión %")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"

    def __str__(self):
        return f"{self.nombre} ({self.comision_porcentaje}%)"


class CotizacionEstado(models.TextChoices):
    PENDIENTE = 'PEND', 'Pendiente'
    ACEPTADA = 'ACEP', 'Aceptada'
    ANULADA = 'ANUL', 'Anulada'


class CondicionVenta(models.TextChoices):
    """Condiciones de venta para la cotización"""
    CONTADO = 'CONT', 'Contado'
    CREDITO = 'CRED', 'Crédito'
    OTRO = 'OTRO', 'Otro'


class Cotizacion(models.Model):
    """Modelo de cotización"""

    numero = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="Número"
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="cotizaciones"
    )

    fecha = models.DateField(
        default=timezone.localdate
    )

    vigencia_hasta = models.DateField(
        default=timezone.localdate
    )

    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    terminos = models.TextField(
        blank=True,
        default=""
    )

    estado = models.CharField(
        max_length=4,
        choices=CotizacionEstado.choices,
        default=CotizacionEstado.PENDIENTE
    )

    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    sucursal = models.CharField(
        max_length=100,
        blank=True,
        default="MATRIZ"
    )

    vendedor = models.ForeignKey(
        Vendedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cotizaciones"
    )

    comision_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        blank=True
    )

    descuento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        blank=True
    )

    recargo_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        blank=True
    )

    glosa = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    observaciones = models.TextField(
        blank=True,
        default=""
    )

    # =========================================
    # NUEVO: Condición de venta
    # =========================================
    condicion_venta = models.CharField(
        max_length=4,
        choices=CondicionVenta.choices,
        default=CondicionVenta.CREDITO,
        verbose_name="Condición de Venta"
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.codigo} - {self.cliente}"

    # =========================================
    # NUMERACIÓN SEGURA
    # =========================================

    @classmethod
    def siguiente_numero(cls):
        ultimo = (
            cls.objects
            .select_for_update()
            .order_by("-numero")
            .first()
        )
        if ultimo and ultimo.numero:
            return ultimo.numero + 1
        return 1

    # =========================================
    # SAVE ROBUSTO
    # =========================================

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                original = Cotizacion.objects.get(pk=self.pk)
                if original.numero != self.numero:
                    raise ValidationError(
                        "El número de cotización no puede modificarse una vez creado."
                    )

            if not self.numero:
                if self.codigo:
                    m = re.search(r"(\d+)$", self.codigo)
                    if m:
                        self.numero = int(m.group(1))

                if not self.numero:
                    self.numero = self.siguiente_numero()

            self.codigo = f"COT-{self.numero:06d}"
            super().save(*args, **kwargs)

    # =========================================
    # TOTALES
    # =========================================

    @property
    def total_items(self):
        return sum((it.total for it in self.items.all()), 0)

    @property
    def total_afecto(self):
        return sum((it.total for it in self.items.all() if not it.exento), 0)

    @property
    def total_exento(self):
        return sum((it.total for it in self.items.all() if it.exento), 0)

    @property
    def iva(self):
        return self.total_afecto * Decimal('0.19')

    @property
    def subtotal(self):
        return self.total_items

    @property
    def descuento_aplicado(self):
        descuento_por_monto = Decimal('0')
        if self.descuento_porcentaje and self.descuento_porcentaje > 0:
            descuento_por_monto = (
                self.subtotal *
                (self.descuento_porcentaje / 100)
            )
        descuento_fijo = self.descuento or Decimal('0')
        return max(descuento_fijo, descuento_por_monto)

    @property
    def recargo_aplicado(self):
        if self.recargo_porcentaje and self.recargo_porcentaje > 0:
            return (
                self.subtotal *
                (self.recargo_porcentaje / 100)
            )
        return Decimal('0')

    @property
    def total_neto(self):
        total = (
            self.subtotal
            - self.descuento_aplicado
            + self.recargo_aplicado
            + self.iva
        )
        return max(total, Decimal('0'))

    # =========================================
    # NUEVO: Método para obtener total de cuotas
    # =========================================
    @property
    def total_cuotas(self):
        return sum((cuota.monto for cuota in self.cuotas.all()), Decimal('0'))


class CotizacionItem(models.Model):
    """Ítems de la cotización"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    titulo = models.CharField(max_length=200)
    unidad = models.CharField(max_length=50, default="Unidad", blank=True)
    cantidad = models.IntegerField(default=1)
    valor_unitario = models.IntegerField(default=0)
    exento = models.BooleanField(default=False)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.titulo} - {self.cantidad} x {self.valor_unitario}"

    @property
    def subtotal(self):
        return self.cantidad * self.valor_unitario

    @property
    def descuento_aplicado(self):
        if self.descuento_porcentaje > 0:
            descuento_por_monto = int(self.subtotal * (self.descuento_porcentaje / 100))
            return max(self.descuento or 0, descuento_por_monto)
        return self.descuento or 0

    @property
    def total(self):
        return self.subtotal - self.descuento_aplicado


# =========================================
# NUEVO: Modelo de cuotas para condición de venta
# =========================================
class CotizacionCuota(models.Model):
    """Cuotas/pagos asociados a la cotización (para crédito)"""
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='cuotas'
    )
    fecha = models.DateField(
        verbose_name="Fecha de cuota"
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto"
    )

    class Meta:
        ordering = ['fecha']
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"

    def __str__(self):
        return f"Cuota {self.fecha}: ${self.monto:,.0f}"