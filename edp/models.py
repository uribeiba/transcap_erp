from decimal import Decimal
import re

from django.db import models
from django.utils import timezone

from bitacora.models import Bitacora
from centro_comercio.models import Cliente


class EDP(models.Model):
    ESTADOS = (
        ("BORR", "Borrador"),
        ("PROC", "En proceso"),
        ("PAGA", "Pagado"),
        ("ANUL", "Anulado"),
    )

    codigo = models.CharField(max_length=20, unique=True)

    # Cabecera del documento
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="edps",
        null=True,
        blank=True,
    )
    fecha_pago = models.DateField(default=timezone.now)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_termino = models.DateField(null=True, blank=True)
    responsable = models.CharField(max_length=150, blank=True, null=True)

    # Snapshots de cabecera del cliente (para PDF histórico)
    razon_social_snapshot = models.CharField(max_length=200, blank=True, null=True)
    rut_snapshot = models.CharField(max_length=20, blank=True, null=True)
    giro_snapshot = models.CharField(max_length=150, blank=True, null=True)

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
        """
        Genera código secuencial: EDP_0001, EDP_0002, etc.
        """
        ultimo_edp = (
            EDP.objects.filter(codigo__regex=r"^EDP_\d+$")
            .order_by("-id")
            .first()
        )

        if not ultimo_edp:
            return "EDP_0001"

        match = re.search(r"EDP_(\d+)", ultimo_edp.codigo)
        if match:
            siguiente_num = int(match.group(1)) + 1
        else:
            siguiente_num = EDP.objects.count() + 1

        return f"EDP_{siguiente_num:04d}"

    def _copiar_snapshot_cliente(self):
        """
        Guarda los datos del cliente al momento de emitir/guardar el EDP.
        Así el PDF no cambia si después editan el cliente.
        """
        if self.cliente:
            self.razon_social_snapshot = self.cliente.razon_social
            self.rut_snapshot = self.cliente.rut
            self.giro_snapshot = getattr(self.cliente, "giro", None)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()

        if self.cliente:
            self._copiar_snapshot_cliente()

        super().save(*args, **kwargs)

    def recalcular_totales(self, iva_rate=Decimal("0.19")):
        lineas = self.items.all()
        neto = sum((Decimal(str(l.total_linea or 0)) for l in lineas), Decimal("0"))
        iva = (neto * Decimal(str(iva_rate))).quantize(Decimal("0.01"))
        total = (neto + iva).quantize(Decimal("0.01"))

        self.neto = neto
        self.iva = iva
        self.total = total
        self.save(update_fields=["neto", "iva", "total"])

    @property
    def razon_social_pdf(self):
        return self.razon_social_snapshot or (self.cliente.razon_social if self.cliente else "")

    @property
    def rut_pdf(self):
        return self.rut_snapshot or (self.cliente.rut if self.cliente else "")

    @property
    def giro_pdf(self):
        return self.giro_snapshot or (getattr(self.cliente, "giro", "") if self.cliente else "")


class EDPServicio(models.Model):
    """
    Se mantiene el nombre del modelo y del campo 'servicio'
    para no romper vistas, forms y templates existentes.

    Pero ahora 'servicio' apunta a Bitacora.
    Además se guardan snapshots para PDF/Excel histórico.
    """
    edp = models.ForeignKey(EDP, related_name="items", on_delete=models.CASCADE)
    servicio = models.ForeignKey(
        Bitacora,
        on_delete=models.PROTECT,
        related_name="edp_items"
    )

    tarifa = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estadia = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Snapshots del detalle
    conductor_snapshot = models.CharField(max_length=150, blank=True, null=True)
    rut_conductor_snapshot = models.CharField(max_length=20, blank=True, null=True)
    tracto_snapshot = models.CharField(max_length=50, blank=True, null=True)
    origen_snapshot = models.CharField(max_length=120, blank=True, null=True)
    destino_snapshot = models.CharField(max_length=120, blank=True, null=True)
    numero_guia_snapshot = models.CharField(max_length=120, blank=True, null=True)

    fecha_carga_snapshot = models.DateField(null=True, blank=True)
    fecha_arribo_snapshot = models.DateField(null=True, blank=True)
    fecha_descarga_snapshot = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.edp.codigo} - Servicio #{self.servicio_id}"

    def _copiar_snapshot_desde_bitacora(self):
        b = self.servicio
        if not b:
            return

        # conductor
        conductor_nombre = ""
        conductor_rut = ""

        conductor = getattr(b, "conductor", None)
        if conductor:
            conductor_nombre = getattr(conductor, "nombre_completo", None) or str(conductor)
            conductor_rut = getattr(conductor, "rut", None) or ""

        self.conductor_snapshot = conductor_nombre or self.conductor_snapshot
        self.rut_conductor_snapshot = conductor_rut or self.rut_conductor_snapshot

        # tracto
        tracto = getattr(b, "tracto", None)
        self.tracto_snapshot = str(tracto) if tracto else self.tracto_snapshot

        # origen / destino
        self.origen_snapshot = getattr(b, "origen", None) or self.origen_snapshot
        self.destino_snapshot = getattr(b, "destino", None) or self.destino_snapshot

        # guía
        self.numero_guia_snapshot = getattr(b, "guias_raw", None) or self.numero_guia_snapshot

        # fechas
        self.fecha_carga_snapshot = getattr(b, "fecha", None) or self.fecha_carga_snapshot
        self.fecha_arribo_snapshot = getattr(b, "fecha_arribo", None) or self.fecha_arribo_snapshot
        self.fecha_descarga_snapshot = getattr(b, "fecha_descarga", None) or self.fecha_descarga_snapshot

    def save(self, *args, **kwargs):
        tarifa = Decimal(str(self.tarifa or 0))
        estadia = Decimal(str(self.estadia or 0))
        self.total_linea = tarifa + estadia

        if self.servicio_id:
            self._copiar_snapshot_desde_bitacora()

        super().save(*args, **kwargs)

    @property
    def conductor_pdf(self):
        if self.conductor_snapshot:
            return self.conductor_snapshot
        conductor = getattr(self.servicio, "conductor", None)
        return getattr(conductor, "nombre_completo", "") if conductor else ""

    @property
    def rut_conductor_pdf(self):
        if self.rut_conductor_snapshot:
            return self.rut_conductor_snapshot
        conductor = getattr(self.servicio, "conductor", None)
        return getattr(conductor, "rut", "") if conductor else ""

    @property
    def tracto_pdf(self):
        if self.tracto_snapshot:
            return self.tracto_snapshot
        return str(self.servicio.tracto) if getattr(self.servicio, "tracto", None) else ""

    @property
    def origen_pdf(self):
        return self.origen_snapshot or getattr(self.servicio, "origen", "") or ""

    @property
    def destino_pdf(self):
        return self.destino_snapshot or getattr(self.servicio, "destino", "") or ""

    @property
    def numero_guia_pdf(self):
        return self.numero_guia_snapshot or getattr(self.servicio, "guias_raw", "") or ""

    @property
    def fecha_carga_pdf(self):
        return self.fecha_carga_snapshot or getattr(self.servicio, "fecha", None)

    @property
    def fecha_arribo_pdf(self):
        return self.fecha_arribo_snapshot or getattr(self.servicio, "fecha_arribo", None)

    @property
    def fecha_descarga_pdf(self):
        return self.fecha_descarga_snapshot or getattr(self.servicio, "fecha_descarga", None)


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

    def __str__(self):
        return f"Pago {self.edp.codigo} - {self.monto}"