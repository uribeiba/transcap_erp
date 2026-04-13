from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.core.exceptions import FieldError
from django.utils import timezone
from datetime import timedelta
from calendar import monthrange
from decimal import Decimal

from facturacion.models import Factura, EstadoFactura
from gastos.models import Gasto

# Importaciones condicionales para evitar errores si los modelos no existen
try:
    from taller.models import DocumentoVehiculo, DocumentoConductor
    TALLER_EXISTS = True
except ImportError:
    TALLER_EXISTS = False

@login_required
def panel_control(request):
    hoy = timezone.localdate()

    # ------------------------------
    # Datos financieros (sin campo 'pagado')
    # ------------------------------
    facturas = Factura.objects.filter(estado__in=[EstadoFactura.EMITIDA, EstadoFactura.ACEPTADA])
    
    # Intenta usar 'monto_moto_total' (el campo que aparece en el error)
    try:
        total_ingresos = facturas.aggregate(total=Sum('monto_moto_total'))['total'] or Decimal(0)
    except FieldError:
        # Fallback: suma neto + IVA
        total_ingresos = facturas.aggregate(
            total=Sum('monto_neto') + Sum('monto_iva')
        )['total'] or Decimal(0)

    total_gastos = Gasto.objects.aggregate(total=Sum('monto_total'))['total'] or Decimal(0)

    # Temporalmente, estos indicadores se muestran como 0
    cuentas_cobrar = Decimal(0)
    cuentas_pagar = Decimal(0)
    flujo_caja = Decimal(0)
    rentabilidad = total_ingresos - total_gastos

    # ------------------------------
    # Gráfico últimos 6 meses
    # ------------------------------
    meses_labels = []
    ventas_mensuales = []
    gastos_mensuales = []

    for i in range(5, -1, -1):
        fecha = hoy.replace(day=1) - timedelta(days=30*i)
        primer_dia = fecha.replace(day=1)
        ultimo_dia = primer_dia.replace(day=monthrange(primer_dia.year, primer_dia.month)[1])

        ventas_mes = Factura.objects.filter(
            fecha_emision__gte=primer_dia,
            fecha_emision__lte=ultimo_dia,
            estado__in=[EstadoFactura.EMITIDA, EstadoFactura.ACEPTADA]
        )
        try:
            ventas = ventas_mes.aggregate(total=Sum('monto_moto_total'))['total'] or Decimal(0)
        except FieldError:
            ventas = ventas_mes.aggregate(
                total=Sum('monto_neto') + Sum('monto_iva')
            )['total'] or Decimal(0)

        gastos_mes = Gasto.objects.filter(
            fecha__gte=primer_dia,
            fecha__lte=ultimo_dia
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal(0)

        meses_labels.append(primer_dia.strftime('%b %Y'))
        ventas_mensuales.append(float(ventas))
        gastos_mensuales.append(float(gastos_mes))

    # ------------------------------
    # Documentos de vehículos y conductores
    # ------------------------------
    vencidos_vehiculos = por_vencer_vehiculos = vencidos_conductores = por_vencer_conductores = 0
    if TALLER_EXISTS:
        vencidos_vehiculos = DocumentoVehiculo.objects.filter(fecha_vencimiento__lt=hoy).count()
        por_vencer_vehiculos = DocumentoVehiculo.objects.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=hoy + timedelta(days=30)
        ).count()
        vencidos_conductores = DocumentoConductor.objects.filter(fecha_vencimiento__lt=hoy).count()
        por_vencer_conductores = DocumentoConductor.objects.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=hoy + timedelta(days=30)
        ).count()

    context = {
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'cuentas_cobrar': cuentas_cobrar,
        'cuentas_pagar': cuentas_pagar,
        'flujo_caja': flujo_caja,
        'rentabilidad': rentabilidad,
        'meses_labels': meses_labels,
        'ventas_mensuales': ventas_mensuales,
        'gastos_mensuales': gastos_mensuales,
        'vencidos_vehiculos': vencidos_vehiculos,
        'por_vencer_vehiculos': por_vencer_vehiculos,
        'vencidos_conductores': vencidos_conductores,
        'por_vencer_conductores': por_vencer_conductores,
        'fecha_limite_por_vencer': hoy + timedelta(days=30),
        'ver_finanzas': True,  # temporal
    }
    return render(request, 'dashboard/panel_control.html', context)