from django.db import models
from django.conf import settings
from django.utils import timezone



class Cliente(models.Model):
    # Versión mínima. Si ya tienes clientes en otra app, luego cambiamos este FK.
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
    """
    1 registro = mezcla guía + factura (flujo por estado).
    Se trabaja por día (fecha).
    """
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

    # Concurrencia (bloqueo por registro)
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
        permissions = [
            ("puede_ver_estado", "Puede ver Estado Facturación/Guías"),
            ("puede_editar_estado", "Puede editar Estado Facturación/Guías"),
            ("puede_desbloquear_estado", "Puede desbloquear registros"),
        ]

    def __str__(self):
        return f"{self.fecha} #{self.correlativo_diario:03d}"

    def esta_bloqueado(self) -> bool:
        return bool(self.bloqueado_por_id and self.bloqueado_desde)

    def bloqueo_expirado(self, minutos=10) -> bool:
        if not self.esta_bloqueado():
            return False
        return timezone.now() - self.bloqueado_desde > timezone.timedelta(minutes=minutos)

    def puede_editar(self, user) -> bool:
        if not self.esta_bloqueado():
            return True
        if self.bloqueo_expirado():
            return True
        return self.bloqueado_por_id == getattr(user, "id", None)

    def bloquear(self, user):
        self.bloqueado_por = user
        self.bloqueado_desde = timezone.now()

    def desbloquear(self):
        self.bloqueado_por = None
        self.bloqueado_desde = None

    @classmethod
    def siguiente_correlativo(cls, fecha):
        ultimo = cls.objects.filter(fecha=fecha).order_by("-correlativo_diario").first()
        return (ultimo.correlativo_diario + 1) if ultimo else 1





class SessionOperaciones(models.Model):
    """
    Presencia multiusuario (quién está conectado / en qué tab/fecha).
    Se actualiza con 'ping' periódico desde el tablero.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sesiones_operaciones",
    )
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)
    fecha = models.DateField(null=True, blank=True, db_index=True)
    tab = models.CharField(max_length=10, blank=True, default="")

    class Meta:
        verbose_name = "Sesión Operaciones"
        verbose_name_plural = "Sesiones Operaciones"
        indexes = [
            models.Index(fields=["last_seen"]),
            models.Index(fields=["fecha", "tab"]),
        ]

    def __str__(self):
        return f"{self.user} ({self.tab}) {self.fecha} - {self.last_seen}"
    
   # ============================================================
# Estatus Operacional de Viajes (AM/PM) - reemplaza planilla Excel
# ============================================================

from taller.models import Conductor, Vehiculo  # noqa: E402


class TurnoEstatus(models.TextChoices):
    AM = "AM", "AM"
    PM = "PM", "PM"


class EstatusOperacionalViaje(models.Model):
    """
    Registro diario por chofer, por fecha y turno (AM/PM).
    Independiente de 'CoordinacionViaje' (opción A).
    """

    fecha = models.DateField(default=timezone.localdate)
    turno = models.CharField(max_length=2, choices=TurnoEstatus.choices, default=TurnoEstatus.AM)

    conductor = models.ForeignKey(
        Conductor, on_delete=models.PROTECT, related_name="estatus_operacional"
    )

    tracto = models.ForeignKey(
        Vehiculo, on_delete=models.PROTECT, null=True, blank=True,
        related_name="estatus_tracto",
        limit_choices_to={"tipo": "TRACTO"},
        help_text="Vehículo tipo TRACTO (patente)."
    )
    rampla = models.ForeignKey(
        Vehiculo, on_delete=models.PROTECT, null=True, blank=True,
        related_name="estatus_rampla",
        limit_choices_to={"tipo": "SEMIRREMOLQUE"},
        help_text="Vehículo tipo SEMIRREMOLQUE (rampla)."
    )

    estado_texto = models.TextField(blank=True, null=True)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="estatus_viajes_creados"
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="estatus_viajes_actualizados"
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
        permissions = [
            ("puede_ver_estatus_viajes", "Puede ver Estatus de Viajes (Operaciones)"),
            ("puede_editar_estatus_viajes", "Puede editar Estatus de Viajes (Operaciones)"),
        ]

    def __str__(self):
        return f"{self.fecha} {self.turno} - {self.conductor}"


# ============================================================
# Estatus de viajes (AM/PM)
# ============================================================

class TurnoEstatus(models.TextChoices):
    AM = "AM", "AM"
    PM = "PM", "PM"


class EstatusOperacionalViaje(models.Model):
    fecha = models.DateField(db_index=True)
    turno = models.CharField(max_length=2, choices=TurnoEstatus.choices, db_index=True)

    # Choferes (tú ya tienes choferes en el sistema)
    conductor = models.ForeignKey("taller.Conductor", on_delete=models.PROTECT, related_name="estatus_viajes")

    # Patentes (si tienes modelos de flota, apuntamos ahí)
    tracto = models.ForeignKey("taller.Vehiculo", on_delete=models.SET_NULL, null=True, blank=True, related_name="estatus_tracto")
    rampla = models.ForeignKey("taller.Vehiculo", on_delete=models.SET_NULL, null=True, blank=True, related_name="estatus_rampla")

    estado_texto = models.TextField(blank=True, default="")

    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="estatus_viajes_creados")
    actualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="estatus_viajes_actualizados")
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("fecha", "turno", "conductor")
        ordering = ["fecha", "turno", "conductor__apellidos", "conductor__nombres"]
        permissions = [
            ("puede_ver_estatus_viajes", "Puede ver estatus de viajes"),
            ("puede_editar_estatus_viajes", "Puede editar estatus de viajes"),
        ]

    def __str__(self):
        return f"{self.fecha} {self.turno} - {self.conductor}"