# suscripciones/models.py
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    max_usuarios = models.PositiveIntegerField(default=1)
    max_empresas = models.PositiveIntegerField(default=1)  # por ahora 1 siempre
    activo = models.BooleanField(default=True)

    # precios (puedes dejar 0 si aún no cobras)
    precio_mensual = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    precio_anual = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    # ✅ NUEVO: para panel pro
    descripcion = models.TextField(blank=True, default="")
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["orden", "max_usuarios", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.max_usuarios} usuarios)"


class Suscripcion(models.Model):
    ESTADOS = (
        ("TRIAL", "Trial"),
        ("ACTIVA", "Activa"),
        ("SUSPENDIDA", "Suspendida"),
        ("VENCIDA", "Vencida"),
        ("CANCELADA", "Cancelada"),
    )

    empresa = models.OneToOneField(
        "parametros.Empresa",
        on_delete=models.CASCADE,
        related_name="suscripcion",          # ✅ oficial
        related_query_name="suscripcion",
    )

    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="suscripciones")

    estado = models.CharField(max_length=12, choices=ESTADOS, default="ACTIVA")
    inicio = models.DateField(default=timezone.now)
    fin = models.DateField(null=True, blank=True)

    limite_usuarios = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-inicio"]

    def save(self, *args, **kwargs):
        if not self.limite_usuarios:
            self.limite_usuarios = self.plan.max_usuarios
        super().save(*args, **kwargs)

    @property
    def vigente_hasta(self):
        return self.fin

    @property
    def vigente(self) -> bool:
        if self.estado != "ACTIVA":
            return False
        if self.fin and self.fin < timezone.now().date():
            return False
        return True

    def aplicar_plan(self, save: bool = False):
        self.limite_usuarios = self.plan.max_usuarios
        if save:
            self.save(update_fields=["limite_usuarios"])
        return self

    def __str__(self):
        return f"{self.empresa} -> {self.plan} ({self.estado})"
