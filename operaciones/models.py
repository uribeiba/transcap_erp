from django.db import models
from django.conf import settings
from django.utils import timezone
from taller.models import Conductor, Vehiculo
from centro_comercio.models import Cliente  # si usas Cliente de centro_comercio

# ============================================================
# CLIENTES Y UBICACIÓN
# ============================================================

class Cliente(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    rut = models.CharField(max_length=15, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ============================================================
# ESTADOS GENERALES (FACTURACIÓN / GUÍA)
# ============================================================

class EstadoRegistro(models.TextChoices):
    PENDIENTE = "PEND", "Pendiente"
    GUIA = "GUIA", "Guía emitida"
    FACTURADO = "FACT", "Facturado"
    PAGADO = "PAGO", "Pagado"
    OBSERVADO = "OBS", "Observado"


class Prioridad(models.TextChoices):
    NORMAL = "NOR", "Normal"
    URGENTE = "URG", "Urgente"


class EstadoFacturacionGuia(models.Model):
    fecha = models.DateField(default=timezone.localdate)
    correlativo_diario = models.PositiveIntegerField(default=1)

    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, null=True, blank=True, related_name="estados"
    )
    origen = models.ForeignKey(
        Ciudad, on_delete=models.PROTECT, null=True, blank=True, related_name="estados_origen"
    )
    destino = models.ForeignKey(
        Ciudad, on_delete=models.PROTECT, null=True, blank=True, related_name="estados_destino"
    )

    nro_guia = models.CharField(max_length=50, blank=True, null=True)
    nro_factura = models.CharField(max_length=50, blank=True, null=True)
    referencia_viaje = models.CharField(max_length=100, blank=True, null=True)

    monto = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    estado = models.CharField(
        max_length=4, choices=EstadoRegistro.choices, default=EstadoRegistro.PENDIENTE
    )
    prioridad = models.CharField(
        max_length=3, choices=Prioridad.choices, default=Prioridad.NORMAL
    )
    observaciones = models.TextField(blank=True, null=True)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="efg_creados"
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="efg_actualizados"
    )

    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    bloqueado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="efg_bloqueados"
    )
    bloqueado_desde = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "estado", "prioridad", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "correlativo_diario"],
                name="uniq_efg_fecha_correlativo",
            )
        ]

    def __str__(self):
        return f"{self.fecha} #{self.correlativo_diario:03d}"


# ============================================================
# SESIONES OPERACIONES
# ============================================================

class SessionOperaciones(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sesiones_operaciones",
    )
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)
    fecha = models.DateField(null=True, blank=True, db_index=True)
    tab = models.CharField(max_length=10, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["last_seen"]),
            models.Index(fields=["fecha", "tab"]),
        ]

    def __str__(self):
        return f"{self.user} ({self.tab}) {self.fecha}"


# ============================================================
# ESTATUS OPERACIONAL DE VIAJES (VERSIÓN FINAL)
# ============================================================

class TurnoEstatus(models.TextChoices):
    AM = "AM", "AM"
    PM = "PM", "PM"


class EstatusOperacionalViaje(models.Model):

    class EstadoCargaChoices(models.TextChoices):
        DESCARGADO = "DESCARGADO", "Descargado"
        CAMINO_DESCARGAR = "CAMINO_DESCARGAR", "Camino a descargar"
        RETORNO_VACIO = "RETORNO_VACIO", "Retorno vacío"
        CARGADO = "CARGADO", "Cargado"
        EN_RUTA = "EN_RUTA", "En ruta"
        OTRO = "OTRO", "Otro"

    fecha = models.DateField(default=timezone.localdate, db_index=True)

    turno = models.CharField(
        max_length=2,
        choices=TurnoEstatus.choices,
        default=TurnoEstatus.AM,
        db_index=True,
    )

    conductor = models.ForeignKey(
        Conductor,
        on_delete=models.PROTECT,
        related_name="estatus_operacional",
    )

    tracto = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="estatus_tracto",
        limit_choices_to={"tipo": "TRACTO"},
    )

    rampla = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="estatus_rampla",
        limit_choices_to={"tipo": "SEMIRREMOLQUE"},
    )

    cliente = models.ForeignKey(
        "centro_comercio.Cliente",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="estatus_viajes",
    )

    nro_guia = models.CharField(max_length=50, blank=True, default="")
    estado_guia = models.CharField(max_length=120, blank=True, default="")

    estado_carga = models.CharField(
        max_length=25,
        choices=EstadoCargaChoices.choices,
        default=EstadoCargaChoices.OTRO,
    )

    lugar_carga = models.CharField(max_length=150, blank=True, default="")
    fecha_carga = models.DateField(null=True, blank=True)

    lugar_descarga = models.CharField(max_length=150, blank=True, default="")
    fecha_descarga = models.DateField(null=True, blank=True)

    estado_texto = models.TextField(blank=True, default="")
    observaciones = models.TextField(blank=True, default="")

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estatus_viajes_creados",
    )

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estatus_viajes_actualizados",
    )

    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "turno", "conductor__apellidos", "conductor__nombres"]
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "turno", "conductor"],
                name="uniq_estatus_fecha_turno_conductor",
            )
        ]

    def __str__(self):
        return f"{self.fecha} {self.turno} - {self.conductor}"
    
    


class Viaje(models.Model):
    # Datos del viaje (planilla AM/PM)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='viajes')
    origen = models.CharField(max_length=200)
    destino = models.CharField(max_length=200)
    fecha_viaje = models.DateField(default=timezone.now)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    facturado = models.BooleanField(default=False)   # ← campo necesario
    # otros campos que ya tengas (chofer, patente, etc.)
    
    def __str__(self):
        return f"{self.origen} → {self.destino} - {self.fecha_viaje}"