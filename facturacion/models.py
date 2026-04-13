# facturacion/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.db.models import Max
from centro_comercio.models import Cliente
from operaciones.models import Viaje   # ojo: si ya no usas Viaje, puedes quitarlo
from bitacora.models import Bitacora   # ← para la relación ManyToMany
from django.utils import timezone

class TipoDTE(models.TextChoices):
    FACTURA_AFECTA = '33', 'Factura Afecta (33)'
    FACTURA_EXENTA = '34', 'Factura Exenta (34)'
    BOLETA = '39', 'Boleta (39)'
    NOTA_CREDITO = '61', 'Nota de Crédito (61)'
    NOTA_DEBITO = '56', 'Nota de Débito (56)'

class EstadoFactura(models.TextChoices):
    BORRADOR = 'BOR', 'Borrador'
    EMITIDA = 'EMI', 'Emitida (sin SII)'
    ENVIADA = 'ENV', 'Enviada al SII'
    ACEPTADA = 'ACE', 'Aceptada por SII'
    RECHAZADA = 'REC', 'Rechazada por SII'
    ANULADA = 'ANU', 'Anulada'

# Modelo Correlativo (opcional, ya no se usa para folios de factura)
class Correlativo(models.Model):
    tipo_dte = models.CharField(max_length=2, choices=TipoDTE.choices, unique=True)
    ultimo_folio = models.IntegerField(default=0)
    anio = models.IntegerField(default=timezone.now().year)

    def __str__(self):
        return f"{self.get_tipo_dte_display()} - Folio actual: {self.ultimo_folio}"

class Factura(models.Model):
    tipo_dte = models.CharField(max_length=2, choices=TipoDTE.choices, default=TipoDTE.FACTURA_AFECTA)
    folio = models.IntegerField(unique=True, blank=True, null=True)
    fecha_emision = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    
    # Emisor
    razon_social_emisor = models.CharField(max_length=200, default="TRANSCAP SpA")
    rut_emisor = models.CharField(max_length=12, default="76.123.456-7")
    giro_emisor = models.CharField(max_length=100, default="Transporte de carga por carretera")
    
    # Receptor
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='facturas')
    razon_social_cliente = models.CharField(max_length=200)
    rut_cliente = models.CharField(max_length=12)
    giro_cliente = models.CharField(max_length=100, blank=True)
    direccion_cliente = models.CharField(max_length=200, blank=True)
    comuna_cliente = models.CharField(max_length=100, blank=True)
    ciudad_cliente = models.CharField(max_length=100, blank=True)
    
    # Totales
    monto_neto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    monto_iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Estado y relaciones
    estado = models.CharField(max_length=3, choices=EstadoFactura.choices, default=EstadoFactura.BORRADOR)
    # Relación con Bitácora (servicios)
    viajes = models.ManyToManyField(Bitacora, related_name='facturas', blank=True)
    observaciones = models.TextField(blank=True)
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_emision']
    
    def save(self, *args, **kwargs):
        # Asignar folio solo cuando la factura cambia de BORRADOR a EMITIDA y no tiene folio
        if not self.folio and self.estado == EstadoFactura.EMITIDA:
            # Calcular el máximo folio existente entre facturas no anuladas
            # (excluimos anuladas para no reutilizar folios)
            max_folio = Factura.objects.exclude(
                estado=EstadoFactura.ANULADA
            ).aggregate(Max('folio'))['folio__max']
            
            if max_folio is None:
                # No hay ninguna factura emitida aún → usar folio inicial configurable
                # El valor por defecto es 1, pero se puede cambiar en settings.py
                inicio = getattr(settings, 'FACTURA_INICIAL_FOLIO', 1)
                self.folio = inicio
            else:
                self.folio = max_folio + 1
        
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        neto = sum(detalle.monto_neto for detalle in self.detalles.all())
        iva = sum(detalle.monto_iva for detalle in self.detalles.all())
        self.monto_neto = neto
        self.monto_iva = iva
        self.monto_total = neto + iva
        self.save(update_fields=['monto_neto', 'monto_iva', 'monto_total'])
    
    def __str__(self):
        return f"{self.get_tipo_dte_display()} N° {self.folio} - {self.cliente}"

class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    descripcion = models.CharField(max_length=300)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(0)])
    unidad = models.CharField(max_length=20, default="VIAJE")
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    monto_neto = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    monto_iva = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.monto_neto = self.cantidad * self.precio_unitario
        if self.factura.tipo_dte == TipoDTE.FACTURA_AFECTA:
            self.monto_iva = self.monto_neto * Decimal('0.19')
        else:
            self.monto_iva = 0
        self.monto_total = self.monto_neto + self.monto_iva
        super().save(*args, **kwargs)
        self.factura.calcular_totales()
    
    def __str__(self):
        return f"{self.descripcion} - {self.cantidad} x {self.precio_unitario}"

class GuiaDespacho(models.Model):
    numero = models.IntegerField(unique=True)
    fecha = models.DateField()
    origen = models.CharField(max_length=200)
    destino = models.CharField(max_length=200)
    factura = models.OneToOneField(Factura, on_delete=models.SET_NULL, null=True, blank=True, related_name='guia')
    
    def __str__(self):
        return f"Guía N° {self.numero}"

    
    
    