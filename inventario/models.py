from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum

User = get_user_model()


class CategoriaProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Productos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UnidadMedida(models.TextChoices):
    UNIDAD = "UN", "Unidad"
    CAJA = "CJ", "Caja"
    PAR = "PR", "Par"
    LITRO = "LT", "Litro"
    KILO = "KG", "Kilo"
    METRO = "MT", "Metro"


class Bodega(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bodega"
        verbose_name_plural = "Bodegas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )
    unidad_medida = models.CharField(
        max_length=2,
        choices=UnidadMedida.choices,
        default=UnidadMedida.UNIDAD,
    )
    stock_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def stock_actual(self, bodega=None):
        """
        Calcula el stock actual usando el modelo Stock,
        que se mantiene con MovimientoInventario.aplicar_al_stock().
        Si se pasa una bodega, retorna el stock sólo en esa bodega.
        """
        qs = self.stocks.all()  # related_name="stocks" en Stock

        if bodega:
            qs = qs.filter(bodega=bodega)

        total = qs.aggregate(total=Sum("cantidad"))["total"] or 0
        return total

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Stock(models.Model):
    """
    Stock actual de un producto en una bodega específica.
    Se actualiza al registrar movimientos de inventario.
    """
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="stocks",
    )
    bodega = models.ForeignKey(
        Bodega,
        on_delete=models.CASCADE,
        related_name="stocks",
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        unique_together = ("producto", "bodega")

    def __str__(self):
        return f"{self.producto} @ {self.bodega}: {self.cantidad}"


class TipoMovimiento(models.TextChoices):
    INGRESO = "ING", "Ingreso"
    SALIDA = "SAL", "Salida"
    AJUSTE = "AJU", "Ajuste"


class MovimientoInventario(models.Model):
    """
    Movimiento tipo kardex. IMPORTANTE:
    - Lo ideal es NO editar ni borrar movimientos en producción,
      así evitamos desajustes de stock.
    """
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(
        max_length=3,
        choices=TipoMovimiento.choices,
        default=TipoMovimiento.INGRESO,
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="movimientos",
    )
    bodega = models.ForeignKey(
        Bodega,
        on_delete=models.PROTECT,
        related_name="movimientos",
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Opcional, para costeo básico.",
    )
    referencia = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Ej: N° OT Taller, N° Viaje, Patente, etc.",
    )
    observacion = models.TextField(blank=True, null=True)
    usuario_registro = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_inventario_registrados",
    )

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ["-fecha"]

    def __str__(self):
        return (
            f"{self.get_tipo_display()} {self.producto} "
            f"{self.cantidad} {self.bodega} ({self.fecha})"
        )

    def aplicar_al_stock(self):
        """
        Aplica el movimiento al stock de la bodega.
        Se llama UNA sola vez al crear el movimiento.
        """
        stock_obj, _ = Stock.objects.get_or_create(
            producto=self.producto,
            bodega=self.bodega,
            defaults={"cantidad": 0},
        )

        if self.tipo == TipoMovimiento.INGRESO:
            stock_obj.cantidad += self.cantidad
        elif self.tipo == TipoMovimiento.SALIDA:
            stock_obj.cantidad -= self.cantidad
        elif self.tipo == TipoMovimiento.AJUSTE:
            # Ajuste: se interpreta como 'dejar' la cantidad exacta.
            stock_obj.cantidad = self.cantidad

        stock_obj.save()

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None
        super().save(*args, **kwargs)
        # Para no complicar con recálculo, solo aplicamos stock al crear
        if es_nuevo:
            self.aplicar_al_stock()
