from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from weasyprint import HTML

from .models import Factura, EstadoFactura, TipoDTE
from .forms import FacturaForm
from operaciones.models import Viaje
from centro_comercio.models import Cliente
from .services.sii_client import enviar_dte_sii

# facturacion/views.py
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required



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

def enviar_factura_sii(request, pk):
    """Envía la factura al SII (simulado por ahora)"""
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

def generar_pdf_factura(request, pk):
    """Genera el PDF de la factura (formato tributario)"""
    factura = get_object_or_404(Factura, pk=pk)
    template = get_template('facturacion/factura_pdf.html')
    html = template.render({'factura': factura})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{factura.folio}.pdf"'
    HTML(string=html).write_pdf(response)
    return response

def obtener_datos_cliente(request, cliente_id):
    """Retorna los datos de un cliente en JSON para autocompletar el formulario"""
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
        data = {
            'razon_social': cliente.razon_social,
            'rut': cliente.rut,
            'giro': cliente.giro or '',
            'direccion': cliente.direccion or '',
            'comuna': cliente.localidad or '',   # mapeamos localidad → comuna
            'ciudad': cliente.localidad or '',   # si no tienes ciudad, usa localidad también
        }
        return JsonResponse(data)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        # Captura cualquier otro error y lo muestra en la consola del navegador
        return JsonResponse({'error': str(e)}, status=500)
    
    

@login_required
def emitir_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if factura.estado == EstadoFactura.BORRADOR:
        factura.estado = EstadoFactura.EMITIDA
        factura.save()  # aquí se asigna el folio automáticamente
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
def informe_facturas(request):
    # Obtener parámetros de filtro
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cliente_id = request.GET.get('cliente')
    estado = request.GET.get('estado')
    tipo_dte = request.GET.get('tipo_dte')

    # Base queryset
    facturas = Factura.objects.select_related('cliente').all()

    # Aplicar filtros
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

    # Totales generales
    total_neto = facturas.aggregate(Sum('monto_neto'))['monto_neto__sum'] or 0
    total_iva = facturas.aggregate(Sum('monto_iva'))['monto_iva__sum'] or 0
    total_final = facturas.aggregate(Sum('monto_total'))['monto_total__sum'] or 0

    # Lista de clientes para el select
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