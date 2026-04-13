from django.contrib import admin
from .models import Factura, DetalleFactura, Correlativo

admin.site.register(Factura)
admin.site.register(DetalleFactura)
admin.site.register(Correlativo)