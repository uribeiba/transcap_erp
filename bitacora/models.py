from django.db import models
from django.conf import settings
from django.utils import timezone
from operaciones.models import EstatusOperacionalViaje


class EstadoBitacora(models.TextChoices):
    VIGENTE = "VIG", "Vigente"
    CERRADA = "CER", "Cerrada"
    ANULADA = "ANU", "Anulada"


class Bitacora(models.Model):
    # =========================
    # Relaciones principales
    # =========================

    cliente = models.ForeignKey(
        "centro_comercio.Cliente",
        on_delete=models.PROTECT,
        related_name="bitacoras",
        null=True,
        blank=True,
    )

    coordinacion = models.ForeignKey(
        "taller.CoordinacionViaje",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras",
    )

    conductor = models.ForeignKey(
        "taller.Conductor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras",
    )

    tracto = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras_tracto",
        limit_choices_to={"tipo": "TRACTO", "activo": True},
    )

    rampla = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras_rampla",
        limit_choices_to={"tipo": "SEMIRREMOLQUE", "activo": True},
    )

    # =========================
    # Datos del viaje
    # =========================

    origen = models.CharField(max_length=120, blank=True, default="")
    intermedio = models.CharField(max_length=120, blank=True, default="")
    destino = models.CharField(max_length=120, blank=True, default="")

    fecha = models.DateField(null=True, blank=True)
    fecha_arribo = models.DateField(null=True, blank=True)
    fecha_descarga = models.DateField(null=True, blank=True)

    # =========================
    # Datos comerciales
    # =========================

    tarifa_flete = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estadia = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # 👉 COORDINADOR = TEXTO LIBRE (lo que tú quieres)
    coordinador = models.CharField(
        max_length=120,
        blank=True,
        default=""
    )

    descripcion_trabajo = models.TextField(blank=True, default="")

    guias_raw = models.CharField(max_length=255, blank=True, default="")
    oc_edp_raw = models.CharField(max_length=255, blank=True, default="")

    estado = models.CharField(
        max_length=3,
        choices=EstadoBitacora.choices,
        default=EstadoBitacora.VIGENTE
    )


    estatus_origen = models.ForeignKey(
    "operaciones.EstatusOperacionalViaje",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="bitacoras_generadas",
    )

    # =========================
    # Auditoría
    # =========================

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras_creadas",
    )

    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-id"]

    def __str__(self):
        cli = getattr(self.cliente, "razon_social", None) or "Sin cliente"
        return f"Bitácora #{self.id} - {cli} ({self.fecha})"

    # =========================
    # Helpers
    # =========================

    @property
    def total(self):
        return (self.tarifa_flete or 0) + (self.estadia or 0)

    def _split_tokens(self, raw: str):
        return [t.strip() for t in (raw or "").split("-") if t.strip()]

    def sync_detalles(self):
        guias = self._split_tokens(self.guias_raw)
        ocs = self._split_tokens(self.oc_edp_raw)

        self.detalles.all().delete()

        max_len = max(len(guias), len(ocs), 1)
        for i in range(max_len):
            BitacoraDetalle.objects.create(
                bitacora=self,
                nro_guia=guias[i] if i < len(guias) else "",
                oc_edp=ocs[i] if i < len(ocs) else "",
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_detalles()


class BitacoraDetalle(models.Model):
    bitacora = models.ForeignKey(
        Bitacora,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    nro_guia = models.CharField(max_length=50, blank=True, default="")
    oc_edp = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.nro_guia} / {self.oc_edp}"
