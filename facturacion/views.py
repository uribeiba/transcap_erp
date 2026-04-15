from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import login_required, permission_required
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from io import BytesIO

from .models import Factura, EstadoFactura, TipoDTE
from .forms import FacturaForm
from operaciones.models import Viaje
from centro_comercio.models import Cliente
from .services.sii_client import enviar_dte_sii


# ---------- VISTAS BASADAS EN CLASES ----------
class FacturaListView(ListView):
    model = Factura
    template_name = 'facturacion/factura_list.html'
    context_object_name = 'facturas'

    def get_queryset(self):
        qs = super().get_queryset()
        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
        return qs

class FacturaCreateView(CreateView):
    model = Factura
    form_class = FacturaForm
    template_name = 'facturacion/factura_form.html'
    success_url = reverse_lazy('facturacion:lista')

    def get_initial(self):
        initial = super().get_initial()
        viajes_ids = self.request.GET.getlist('viajes')
        if viajes_ids:
            viajes = Viaje.objects.filter(id__in=viajes_ids, facturado=False)
            if viajes.exists():
                initial['cliente'] = viajes.first().cliente
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        for viaje in form.cleaned_data.get('viajes', []):
            viaje.facturado = True
            viaje.save()
        return response

class FacturaDetailView(DetailView):
    model = Factura
    template_name = 'facturacion/factura_detail.html'

class FacturaUpdateView(UpdateView):
    model = Factura
    form_class = FacturaForm
    template_name = 'facturacion/factura_form.html'
    success_url = reverse_lazy('facturacion:lista')


# ---------- VISTAS BASADAS EN FUNCIONES ----------
@login_required
def enviar_factura_sii(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if factura.estado == EstadoFactura.EMITIDA:
        aceptado, mensaje, track_id = enviar_dte_sii(factura)
        if aceptado:
            factura.estado = EstadoFactura.ACEPTADA
            factura.save()
            messages.success(request, f"✅ Factura enviada al SII. Track ID: {track_id}")
        else:
            factura.estado = EstadoFactura.RECHAZADA
            factura.save()
            messages.error(request, f"❌ Error SII: {mensaje}")
    else:
        messages.warning(request, "⚠️ La factura no está en estado EMITIDA")
    return redirect('facturacion:detalle', pk=pk)


@login_required
def generar_pdf_factura(request, pk):
    """Genera PDF de factura usando ReportLab"""
    factura = get_object_or_404(Factura, pk=pk)
    
    # Crear buffer y canvas
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 20 * mm
    y = height - 20 * mm
    
    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(x, y, f"{factura.get_tipo_dte_display()} N° {factura.folio}")
    y -= 10 * mm
    
    # Emisor
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Emisor:")
    y -= 5 * mm
    p.setFont("Helvetica", 10)
    p.drawString(x, y, f"{factura.razon_social_emisor}")
    y -= 4 * mm
    p.drawString(x, y, f"RUT: {factura.rut_emisor}")
    y -= 4 * mm
    p.drawString(x, y, f"Giro: {factura.giro_emisor}")
    y -= 10 * mm
    
    # Receptor
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Receptor:")
    y -= 5 * mm
    p.setFont("Helvetica", 10)
    p.drawString(x, y, f"{factura.razon_social_cliente}")
    y -= 4 * mm
    p.drawString(x, y, f"RUT: {factura.rut_cliente}")
    y -= 4 * mm
    p.drawString(x, y, f"Dirección: {factura.direccion_cliente}, {factura.comuna_cliente}, {factura.ciudad_cliente}")
    y -= 10 * mm
    
    # Detalles
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Detalle:")
    y -= 5 * mm
    
    # Encabezados de tabla
    p.setFont("Helvetica-Bold", 9)
    p.drawString(x, y, "Descripción")
    p.drawString(x + 80 * mm, y, "Cant.")
    p.drawString(x + 100 * mm, y, "Precio")
    p.drawString(x + 130 * mm, y, "Total")
    y -= 5 * mm
    p.line(x, y, x + 170 * mm, y)
    y -= 4 * mm
    
    p.setFont("Helvetica", 9)
    for detalle in factura.detalles.all():
        p.drawString(x, y, detalle.descripcion[:40])
        p.drawString(x + 80 * mm, y, str(detalle.cantidad))
        p.drawString(x + 100 * mm, y, f"${detalle.precio_unitario:,.0f}")
        p.drawString(x + 130 * mm, y, f"${detalle.monto_total:,.0f}")
        y -= 5 * mm
        if y < 50 * mm:
            p.showPage()
            y = height - 20 * mm
            p.setFont("Helvetica", 9)
    
    y -= 5 * mm
    p.line(x, y, x + 170 * mm, y)
    y -= 4 * mm
    
    # Totales
    p.setFont("Helvetica-Bold", 10)
    p.drawString(x + 100 * mm, y, f"Neto: ${factura.monto_neto:,.0f}")
    y -= 5 * mm
    p.drawString(x + 100 * mm, y, f"IVA (19%): ${factura.monto_iva:,.0f}")
    y -= 5 * mm
    p.drawString(x + 100 * mm, y, f"Total: ${factura.monto_total:,.0f}")
    
    # Pie de página
    y = 20 * mm
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(x, y, "Documento generado por Transcap ERP - www.transcap.cl")
    
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{factura.folio}.pdf"'
    response.write(buffer.getvalue())
    return response


@login_required
def obtener_datos_cliente(request, cliente_id):
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
        data = {
            'razon_social': cliente.razon_social,
            'rut': cliente.rut,
            'giro': cliente.giro or '',
            'direccion': cliente.direccion or '',
            'comuna': cliente.localidad or '',
            'ciudad': cliente.localidad or '',
        }
        return JsonResponse(data)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)


@login_required
def informe_facturas(request):
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cliente_id = request.GET.get('cliente')
    estado = request.GET.get('estado')
    tipo_dte = request.GET.get('tipo_dte')

    facturas = Factura.objects.select_related('cliente').all()
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            facturas = facturas.filter(fecha_emision__gte=fecha_desde_obj)
        except:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            facturas = facturas.filter(fecha_emision__lte=fecha_hasta_obj)
        except:
            pass
    if cliente_id and cliente_id != '':
        facturas = facturas.filter(cliente_id=cliente_id)
    if estado and estado != '':
        facturas = facturas.filter(estado=estado)
    if tipo_dte and tipo_dte != '':
        facturas = facturas.filter(tipo_dte=tipo_dte)

    total_neto = facturas.aggregate(Sum('monto_neto'))['monto_neto__sum'] or 0
    total_iva = facturas.aggregate(Sum('monto_iva'))['monto_iva__sum'] or 0
    total_final = facturas.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    clientes = Cliente.objects.all().order_by('razon_social')

    context = {
        'facturas': facturas.order_by('-fecha_emision'),
        'total_neto': total_neto,
        'total_iva': total_iva,
        'total_final': total_final,
        'clientes': clientes,
        'filtros': {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'cliente_id': cliente_id,
            'estado': estado,
            'tipo_dte': tipo_dte,
        },
        'estados': EstadoFactura.choices,
        'tipos_dte': TipoDTE.choices,
    }
    return render(request, 'facturacion/informe_facturas.html', context)


@login_required
def emitir_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if factura.estado == EstadoFactura.BORRADOR:
        factura.estado = EstadoFactura.EMITIDA
        factura.save()
        messages.success(request, f'Factura N° {factura.folio} emitida correctamente.')
    else:
        messages.warning(request, 'La factura ya no está en estado borrador.')
    return redirect('facturacion:lista')


@login_required
def eliminar_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if factura.estado == EstadoFactura.BORRADOR:
        factura.delete()
        messages.success(request, 'Factura eliminada correctamente.')
    else:
        messages.error(request, 'No se puede eliminar una factura que ya ha sido emitida.')
    return redirect('facturacion:lista')


@login_required
def anular_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if factura.estado in [EstadoFactura.EMITIDA, EstadoFactura.ENVIADA, EstadoFactura.ACEPTADA]:
        factura.estado = EstadoFactura.ANULADA
        factura.save()
        messages.success(request, f'Factura N° {factura.folio} ha sido anulada correctamente.')
    else:
        messages.warning(request, 'No se puede anular esta factura.')
    return redirect('facturacion:lista')