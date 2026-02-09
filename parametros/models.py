from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    creada_el = models.DateTimeField(auto_now_add=True)
    actualizada_el = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Empresa(models.Model):
    razon_social = models.CharField(max_length=180)
    rut = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to="empresas/logos/", blank=True, null=True)

    creada_el = models.DateTimeField(auto_now_add=True)
    actualizada_el = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.razon_social


class Sucursal(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="sucursales")
    nombre = models.CharField(max_length=120)

    class Meta:
        unique_together = [("empresa", "nombre")]
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} — {self.empresa.razon_social}"


class RolUsuario(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    USER = "USER", "Usuario"


class Perfil(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="perfiles")
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True, related_name="perfiles")
    rol = models.CharField(max_length=20, choices=RolUsuario.choices, default=RolUsuario.USER)

    def __str__(self):
        return f"{self.user} ({self.rol})"


# ============================
# ⚠️ DUPLICADO SaaS (PARAMETROS)
# ============================
# Nota: Este Plan/Suscripcion chocaba con suscripciones.Plan/Suscripcion.
# Para NO romper ahora, solo evitamos colisión de reverse accessor en Empresa.
# El “oficial” ideal debe vivir en app suscripciones.
# ============================

class Plan(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    max_usuarios = models.PositiveIntegerField(default=1)
    precio_mensual = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    descripcion = models.TextField(blank=True, default="")
    orden = models.PositiveIntegerField(default=1)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "max_usuarios", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.max_usuarios} usuarios)"


class Suscripcion(models.Model):
    ESTADOS = (
        ("ACTIVA", "Activa"),
        ("SUSPENDIDA", "Suspendida"),
        ("VENCIDA", "Vencida"),
    )

    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.CASCADE,
        # ✅ CAMBIO CLAVE: ya NO es "suscripcion" (ese lo deja libre para suscripciones.Suscripcion)
        related_name="suscripcion_parametros",
        related_query_name="suscripcion_parametros",
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="ACTIVA")

    # “copia” del plan para congelar el límite aunque cambie el plan después
    limite_usuarios = models.PositiveIntegerField(default=1)

    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.empresa} -> {self.plan} ({self.estado})"

    @property
    def vigente_hasta(self):
        return self.fecha_fin

    def aplicar_plan(self):
        """Sincroniza límite con el plan actual."""
        self.limite_usuarios = self.plan.max_usuarios
        return self
