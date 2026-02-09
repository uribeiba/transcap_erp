from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from .models import Servicio
from .forms import ServicioForm
from centro_comercio.models import Cotizacion

# Panel principal de servicios
@login_required
def servicios_panel(request):
    return render(request, 'servicios/panel.html')

# Lista de servicios (para carga AJAX)
@login_required
@require_GET
def servicios_lista(request):
    # Filtros
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    
    queryset = Servicio.objects.select_related(
        'cotizacion', 
        'cotizacion__cliente'
    ).all().order_by('-fecha_inicio', '-creado_en')
    
    # Aplicar filtros
    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q) |
            Q(cotizacion__codigo__icontains=q) |
            Q(cotizacion__cliente__razon_social__icontains=q) |
            Q(descripcion__icontains=q)
        )
    
    if estado:
        queryset = queryset.filter(estado=estado)
    
    context = {
        'servicios': queryset,
        'q': q,
        'estado': estado,
        'estados': Servicio.ESTADOS_SERVICIO,
    }
    
    return render(request, 'servicios/_tabla.html', context)

# Detalle de servicio
@login_required
def servicio_detalle(request, pk):
    servicio = get_object_or_404(
        Servicio.objects.select_related(
            'cotizacion',
            'cotizacion__cliente'
        ),
        pk=pk
    )
    return render(request, 'servicios/_detalle.html', {'servicio': servicio})

# Formulario de creación/edición
@login_required
def servicio_form(request, pk=None):
    servicio = None
    if pk:
        servicio = get_object_or_404(Servicio, pk=pk)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            saved = form.save()
            
            # Si es AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True, 
                    'id': saved.id,
                    'codigo': saved.codigo
                })
            
            # Redirigir al panel y abrir el detalle
            return redirect(
                f"{reverse('servicios:servicios_panel')}?open={saved.id}"
            )
        else:
            # Errores en el formulario
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': False, 
                    'errors': form.errors
                }, status=400)
    
    else:
        form = ServicioForm(instance=servicio)
    
    context = {
        'form': form,
        'servicio': servicio,
        'nuevo': pk is None
    }
    return render(request, 'servicios/_form.html', context)

# Eliminar servicio
@login_required
@require_POST
def servicio_eliminar(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    servicio.delete()
    return JsonResponse({'ok': True})

# Vista para crear nuevo servicio desde cotización específica
@login_required
def servicio_nuevo_desde_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_id)
    
    # Crear servicio con datos iniciales de la cotización
    servicio = Servicio(
        codigo=Servicio.siguiente_codigo(),
        cotizacion=cotizacion,
        fecha_inicio=timezone.localdate(),
        fecha_termino=timezone.localdate(),
    )
    
    form = ServicioForm(instance=servicio)
    
    context = {
        'form': form,
        'cotizacion': cotizacion,
        'nuevo': True
    }
    return render(request, 'servicios/_form.html', context)