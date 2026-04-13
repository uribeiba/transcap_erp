from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

class Proveedor(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=200)
    giro = models.CharField(max_length=100, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    contacto_nombre = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['razon_social']
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"

class OrdenCompra(models.Model):
    ESTADO_CHOICES = [
        ('BOR', 'Borrador'),
        ('ENV', 'Enviada'),
        ('PAR', 'Recibida parcial'),
        ('TOT', 'Recibida total'),
        ('ANU', 'Anulada'),
    ]
    numero = models.CharField(max_length=20, unique=True, blank=True)
    fecha = models.DateField(default=timezone.localdate)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    estado = models.CharField(max_length=3, choices=ESTADO_CHOICES, default='BOR')
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = OrdenCompra.objects.order_by('-id').first()
            if ultimo and ultimo.numero:
                try:
                    num = int(ultimo.numero.split('-')[-1]) + 1
                except:
                    num = 1
            else:
                num = 1
            self.numero = f"OC-{num:06d}"
        super().save(*args, **kwargs)

    def total(self):
        return sum(d.subtotal() for d in self.detalles.all())

    def __str__(self):
        return f"{self.numero} - {self.proveedor.razon_social}"

class DetalleOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('inventario.Producto', on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def subtotal(self):
        return self.total

    def __str__(self):
        return f"{self.descripcion} - {self.cantidad} x {self.precio_unitario}"