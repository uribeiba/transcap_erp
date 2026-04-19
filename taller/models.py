from django.db import models
from django.db.models import Sum
from django.utils import timezone


# ============================================
# VEHÍCULOS Y REMOLQUES
# ============================================

class Vehiculo(models.Model):
    ESTADO_CHOICES = [
        ("ACTIVO", "Activo"),
        ("EN_TALLER", "En taller"),
        ("FUERA_SERVICIO", "Fuera de servicio"),
    ]

    TIPO_CHOICES = [
        ("TRACTO", "Tracto camión"),
        ("CAMION", "Camión"),
        ("CAMIONETA", "Camioneta"),
        ("AUTOMOVIL", "Automóvil"),
        ("SEMIRREMOLQUE", "Semirremolque / rampla"),
        ("OTRO", "Otro"),
    ]

    ESTADO_EQUIPO_CHOICES = [
        ("NUEVO", "Nuevo sin uso"),
        ("USADO", "Usado"),
        ("REACONDICIONADO", "Reacondicionado"),
    ]

    patente = models.CharField("Patente", max_length=15, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveIntegerField("Año", blank=True, null=True)

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="CAMION",
        help_text="Ej: Tracto, camión, semirremolque, etc.",
    )

    km_actual = models.PositiveIntegerField(
        "Kilometraje actual", blank=True, null=True
    )
    nro_motor = models.CharField("N° motor", max_length=50, blank=True, null=True)
    nro_chasis = models.CharField("N° chasis", max_length=50, blank=True, null=True)

    capacidad = models.CharField(
        max_length=50, blank=True, null=True, help_text="Toneladas / pasajeros, etc."
    )

    fecha_compra = models.DateField(blank=True, null=True)
    aseguradora = models.CharField(
        max_length=100, blank=True, null=True, help_text="Compañía de seguros"
    )

    descripcion_equipo = models.CharField(
        "Descripción equipo", max_length=150, blank=True, null=True
    )
    estado_equipo = models.CharField(
        "Estado equipo",
        max_length=20,
        choices=ESTADO_EQUIPO_CHOICES,
        blank=True,
        null=True,
        help_text="Ej: Nuevo sin uso, usado, etc.",
    )
    tipo_remolque = models.CharField(
        "Tipo semirremolque",
        max_length=100,
        blank=True,
        null=True,
        help_text="Ej: Plataforma, baranda, rampla, etc.",
    )

    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="ACTIVO"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ["patente"]

    def __str__(self):
        return f"{self.patente} - {self.marca} {self.modelo}"


class Remolque(models.Model):
    """
    Modelo específico para remolques y semirremolques.
    Se deja para compatibilidad con formularios / vistas antiguos.
    """
    codigo = models.CharField("Código interno", max_length=20, unique=True)
    patente = models.CharField(
        "Patente semirremolque",
        max_length=10,
        unique=True,
    )
    descripcion = models.CharField("Descripción", max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Remolque / Semirremolque"
        verbose_name_plural = "Remolques / Semirremolques"
        ordering = ["patente"]

    def __str__(self):
        return f"{self.patente} ({self.codigo})"


# ============================================
# TALLERES / CONDUCTORES
# ============================================

class Taller(models.Model):
    nombre = models.CharField(max_length=150)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Taller"
        verbose_name_plural = "Talleres"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Conductor(models.Model):
    ACTIVO_CHOICES = [
        (True, "Activo"),
        (False, "Inactivo"),
    ]

    TIPO_FICHA_CHOICES = [
        ('EMPLEADO', 'Empleado'),
        ('PROVEEDOR', 'Proveedor'),
        ('CLIENTE_PROVEEDOR', 'Cliente - Proveedor'),
        ('CLIENTE', 'Cliente'),
        ('HONORARIO', 'Honorario'),
    ]

    rut = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    fecha_ingreso = models.DateField(blank=True, null=True)
    licencia_clase = models.CharField(
        max_length=20, blank=True, null=True, help_text="Ej: A2, A3, A5, etc."
    )
    licencia_vencimiento = models.DateField(
        blank=True, null=True, help_text="Fecha de vencimiento de la licencia"
    )

    activo = models.BooleanField(default=True, choices=ACTIVO_CHOICES)
    
    # Relación con el usuario de Django para autenticación
    usuario = models.OneToOneField(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conductor'
    )
    
    # ✅ NUEVO: Tipo de ficha
    tipo_ficha = models.CharField(
        max_length=20,
        choices=TIPO_FICHA_CHOICES,
        default='EMPLEADO',
        blank=True,
        null=True,
        help_text="Tipo de ficha del conductor"
    )

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.rut})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

# ============================================
# DOCUMENTOS
# ============================================

class DocumentoVehiculo(models.Model):
    TIPO_CHOICES = [
        ("PERMISO", "Permiso de circulación"),
        ("REVISION", "Revisión técnica"),
        ("SEGURO_OBL", "Seguro obligatorio"),
        ("SEGURO_VOL", "Seguro voluntario"),
        ("OTRO", "Otro"),
    ]

    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, related_name="documentos"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField()
    archivo = models.FileField(
        upload_to="documentos/vehiculos/", blank=True, null=True
    )

    class Meta:
        verbose_name = "Documento de vehículo"
        verbose_name_plural = "Documentos de vehículos"
        ordering = ["vehiculo", "fecha_vencimiento"]

    def __str__(self):
        return f"{self.vehiculo.patente} - {self.get_tipo_display()}"

    @property
    def esta_vencido(self):
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < timezone.now().date()

    @property
    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - timezone.now().date()).days


class DocumentoConductor(models.Model):
    TIPO_CHOICES = [
        ("LICENCIA", "Licencia de conducir"),
        ("CERT_MED", "Certificado médico"),
        ("OTRO", "Otro"),
    ]

    conductor = models.ForeignKey(
        Conductor, on_delete=models.CASCADE, related_name="documentos"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    archivo = models.FileField(
        upload_to="documentos/conductores/", blank=True, null=True
    )

    class Meta:
        verbose_name = "Documento de conductor"
        verbose_name_plural = "Documentos de conductores"
        ordering = ["conductor", "fecha_vencimiento"]

    def __str__(self):
        return f"{self.conductor} - {self.get_tipo_display()}"

    @property
    def esta_vencido(self):
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < timezone.now().date()


# ============================================
# MANTENIMIENTOS
# ============================================

class Mantenimiento(models.Model):
    TIPO_MANTENIMIENTO = [
        ("PREVENTIVO", "Preventivo"),
        ("CORRECTIVO", "Correctivo"),
        ("OTRO", "Otro"),
    ]

    ESTADO_CHOICES = [
        ("PENDIENTE", "Pendiente"),
        ("EN_PROCESO", "En proceso"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]

    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, related_name="mantenimientos"
    )
    taller = models.ForeignKey(
        Taller,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="mantenimientos",
    )

    fecha_programada = models.DateField(blank=True, null=True)
    fecha_real = models.DateField(blank=True, null=True)

    km_programado = models.PositiveIntegerField(
        "Kilometraje programado", blank=True, null=True
    )
    km_real = models.PositiveIntegerField(
        "Kilometraje real", blank=True, null=True
    )

    tipo = models.CharField(
        max_length=20, choices=TIPO_MANTENIMIENTO, default="PREVENTIVO"
    )
    descripcion = models.TextField(blank=True, null=True)

    costo_mano_obra = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, default=0
    )
    costo_repuestos = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, default=0
    )
    costo_total = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, default=0
    )

    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="PENDIENTE"
    )

    class Meta:
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"
        ordering = ["-fecha_programada", "-fecha_real"]

    def __str__(self):
        return f"{self.vehiculo} - {self.tipo} ({self.estado})"

    def recalcular_costos(self, guardar=True):
        total_repuestos = self.repuestos.aggregate(
            total=Sum("costo_total")
        )["total"] or 0

        self.costo_repuestos = total_repuestos
        self.costo_total = (self.costo_mano_obra or 0) + (self.costo_repuestos or 0)

        if guardar and self.pk:
            Mantenimiento.objects.filter(pk=self.pk).update(
                costo_repuestos=self.costo_repuestos,
                costo_total=self.costo_total,
            )

    def save(self, *args, **kwargs):
        if self.costo_mano_obra is None:
            self.costo_mano_obra = 0
        if self.costo_repuestos is None:
            self.costo_repuestos = 0
        self.costo_total = (self.costo_mano_obra or 0) + (self.costo_repuestos or 0)
        super().save(*args, **kwargs)


class RepuestoMantenimiento(models.Model):
    """
    Repuestos utilizados en un mantenimiento específico.
    Al crear uno nuevo:
    - toma costo_unitario desde el último movimiento de inventario con costo
    - guarda snapshot del costo en esta línea
    - genera salida en inventario
    - recalcula costo del mantenimiento
    """
    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name="repuestos"
    )
    producto = models.ForeignKey(
        "inventario.Producto",
        on_delete=models.PROTECT,
        related_name="repuestos_mantenimientos"
    )
    bodega = models.ForeignKey(
        "inventario.Bodega",
        on_delete=models.PROTECT,
        related_name="repuestos_mantenimientos"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    costo_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = "Repuesto utilizado en mantenimiento"
        verbose_name_plural = "Repuestos utilizados en mantenimientos"

    def __str__(self):
        return f"{self.producto} x {self.cantidad} (Mant. {self.mantenimiento.id})"

    def obtener_costo_unitario_desde_inventario(self):
        from inventario.models import MovimientoInventario

        movimiento = (
            MovimientoInventario.objects.filter(
                producto=self.producto,
                bodega=self.bodega,
                costo_unitario__isnull=False,
            )
            .exclude(costo_unitario=0)
            .order_by("-fecha", "-id")
            .first()
        )

        if not movimiento:
            movimiento = (
                MovimientoInventario.objects.filter(
                    producto=self.producto,
                    costo_unitario__isnull=False,
                )
                .exclude(costo_unitario=0)
                .order_by("-fecha", "-id")
                .first()
            )

        return movimiento.costo_unitario if movimiento else 0

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None

        if not self.costo_unitario:
            self.costo_unitario = self.obtener_costo_unitario_desde_inventario()

        self.costo_total = (self.cantidad or 0) * (self.costo_unitario or 0)

        super().save(*args, **kwargs)

        if es_nuevo:
            from inventario.models import MovimientoInventario, TipoMovimiento

            MovimientoInventario.objects.create(
                tipo=TipoMovimiento.SALIDA,
                producto=self.producto,
                bodega=self.bodega,
                cantidad=self.cantidad,
                costo_unitario=self.costo_unitario,
                referencia=f"Mantención #{self.mantenimiento.id} - {self.mantenimiento.vehiculo.patente}",
                usuario_registro=getattr(self.mantenimiento, "usuario", None),
            )

        self.mantenimiento.recalcular_costos()


# ============================================
# MULTAS
# ============================================

class MultaConductor(models.Model):
    ESTADO_CHOICES = [
        ("PENDIENTE", "Pendiente"),
        ("PAGADA", "Pagada"),
    ]

    conductor = models.ForeignKey(
        Conductor, on_delete=models.CASCADE, related_name="multas"
    )
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="multas",
    )

    fecha = models.DateField()
    infraccion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES, default="PENDIENTE"
    )
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Multa de conductor"
        verbose_name_plural = "Multas de conductores"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.conductor} - {self.infraccion} ({self.monto})"


# ============================================
# RUTAS Y COORDINACIÓN DE VIAJES
# Se mantienen por compatibilidad temporal.
# Ya no deberían usarse como flujo principal en Taller.
# ============================================

class RutaViaje(models.Model):
    nombre = models.CharField("Nombre de la ruta", max_length=100)
    origen = models.CharField("Origen", max_length=100)
    destino = models.CharField("Destino", max_length=100)

    distancia_km = models.DecimalField(
        "Distancia estimada (km)", max_digits=7, decimal_places=2, blank=True, null=True
    )
    duracion_estimada = models.DurationField(
        "Duración estimada",
        blank=True,
        null=True,
        help_text="Ej: 2:30:00 para 2 horas 30 min",
    )
    peajes_aprox = models.DecimalField(
        "Peajes aprox. ($)", max_digits=10, decimal_places=2, blank=True, null=True
    )
    observaciones = models.TextField("Observaciones", blank=True)

    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ruta de viaje"
        verbose_name_plural = "Rutas de viaje"
        ordering = ["origen", "destino", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.origen} → {self.destino})"


class CoordinacionViaje(models.Model):
    ESTADO_VIAJE = [
        ("PLANIFICADO", "Planificado"),
        ("EN_CURSO", "En curso"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]

    fecha_carga = models.DateField("Fecha carga")
    fecha_descarga = models.DateField("Fecha descarga", blank=True, null=True)
    sobreestadia_dias = models.PositiveIntegerField(
        "Sobreestadia (días)", blank=True, null=True
    )

    ruta = models.ForeignKey(
        RutaViaje,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coordinaciones",
    )

    origen = models.CharField(max_length=100, blank=True, null=True)
    destino = models.CharField(max_length=100, blank=True, null=True)

    estado = models.CharField(
        max_length=20, choices=ESTADO_VIAJE, default="PLANIFICADO"
    )

    conductor = models.ForeignKey(
        Conductor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="viajes_coordinados",
    )

    tracto_camion = models.ForeignKey(
        Vehiculo,
        related_name="viajes_tracto",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        limit_choices_to={"tipo": "TRACTO", "activo": True},
    )

    semirremolque = models.ForeignKey(
        Vehiculo,
        related_name="viajes_semirremolque",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        limit_choices_to={"tipo": "SEMIRREMOLQUE", "activo": True},
    )

    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Coordinación de viaje"
        verbose_name_plural = "Coordinaciones de viaje"
        ordering = ["-fecha_carga"]

    def __str__(self):
        return f"{self.fecha_carga} - {self.origen} → {self.destino}"