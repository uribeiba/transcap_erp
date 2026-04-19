from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from .models import GastoCombustible, GastoPeaje, CostoViaje
from .forms import GastoCombustibleForm, GastoPeajeForm, CostoViajeForm
from taller.models import Vehiculo, Conductor





def es_administrador(user):
    if user.is_superuser:
        return True
    if hasattr(user, 'rol_usuario') and user.rol_usuario.rol.nombre == 'Administrador':
        return True
    return False


@login_required
@user_passes_test(es_administrador)
def dashboard_estadisticas(request):
    hoy = timezone.now().date()
    mes_actual = hoy.replace(day=1)
    
    # Resúmenes (igual que antes)
    gasto_combustible_mes = GastoCombustible.objects.filter(fecha__gte=mes_actual).aggregate(
        total_litros=Sum('litros'), total_monto=Sum('monto')
    )
    gasto_peajes_mes = GastoPeaje.objects.filter(fecha__gte=mes_actual).aggregate(total_monto=Sum('monto'))
    costos_viaje_mes = CostoViaje.objects.filter(fecha__gte=mes_actual).aggregate(
        total_combustible=Sum('total_combustible'), total_peajes=Sum('total_peajes'),
        total_mantencion=Sum('total_mantencion'), total_km=Sum('km_recorridos'), total_costo=Sum('costo_total')
    )
    
    # Rankings
    ranking_combustible = GastoCombustible.objects.values('vehiculo__patente', 'vehiculo__marca', 'vehiculo__modelo').annotate(
        total_litros=Sum('litros'), total_monto=Sum('monto')
    ).order_by('-total_monto')[:10]
    
    ranking_peajes = GastoPeaje.objects.values('vehiculo__patente', 'vehiculo__marca', 'vehiculo__modelo').annotate(
        total_monto=Sum('monto')
    ).order_by('-total_monto')[:10]
    
    ranking_costos_viaje = CostoViaje.objects.values('vehiculo__patente', 'vehiculo__marca', 'vehiculo__modelo').annotate(
        total_costo=Sum('costo_total'), total_km=Sum('km_recorridos'), cantidad_viajes=Count('id')
    ).order_by('-total_costo')[:10]
    
    ranking_conductores = CostoViaje.objects.values('conductor__id', 'conductor__nombres', 'conductor__apellidos').annotate(
        total_costo=Sum('costo_total'), total_km=Sum('km_recorridos'), cantidad_viajes=Count('id')
    ).order_by('-total_costo')[:10]
    
    context = {
        'gasto_combustible_mes': {
            'litros': gasto_combustible_mes.get('total_litros') or 0,
            'monto': gasto_combustible_mes.get('total_monto') or 0,
        },
        'gasto_peajes_mes': gasto_peajes_mes.get('total_monto') or 0,
        'costos_viaje_mes': {
            'combustible': costos_viaje_mes.get('total_combustible') or 0,
            'peajes': costos_viaje_mes.get('total_peajes') or 0,
            'mantencion': costos_viaje_mes.get('total_mantencion') or 0,
            'km': costos_viaje_mes.get('total_km') or 0,
            'total': costos_viaje_mes.get('total_costo') or 0,
        },
        'ranking_combustible': ranking_combustible,
        'ranking_peajes': ranking_peajes,
        'ranking_costos_viaje': ranking_costos_viaje,
        'ranking_conductores': ranking_conductores,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_passes_test(es_administrador)
def cargar_combustible(request):
    if request.method == 'POST':
        form = GastoCombustibleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto de combustible registrado correctamente.')
            return redirect('analytics:dashboard')
    else:
        form = GastoCombustibleForm()
    
    return render(request, 'analytics/cargar_combustible.html', {'form': form, 'titulo': 'Cargar Combustible'})


@login_required
@user_passes_test(es_administrador)
def cargar_peaje(request):
    if request.method == 'POST':
        form = GastoPeajeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto de peaje registrado correctamente.')
            return redirect('analytics:dashboard')
    else:
        form = GastoPeajeForm()
    
    return render(request, 'analytics/cargar_peaje.html', {'form': form, 'titulo': 'Cargar Peaje'})


@login_required
@user_passes_test(es_administrador)
def cargar_costo_viaje(request):
    if request.method == 'POST':
        form = CostoViajeForm(request.POST)
        if form.is_valid():
            costo = form.save(commit=False)
            costo.calcular_costo_total()
            costo.save()
            messages.success(request, 'Costo de viaje registrado correctamente.')
            return redirect('analytics:dashboard')
    else:
        form = CostoViajeForm()
    
    return render(request, 'analytics/cargar_costo_viaje.html', {'form': form, 'titulo': 'Cargar Costo de Viaje'})



def es_administrador(user):
    if user.is_superuser:
        return True
    if hasattr(user, 'rol_usuario') and user.rol_usuario.rol.nombre == 'Administrador':
        return True
    return False


@login_required
@user_passes_test(es_administrador)
def dashboard_estadisticas(request):
    hoy = timezone.now().date()
    mes_actual = hoy.replace(day=1)
    
    gasto_combustible_mes = GastoCombustible.objects.filter(fecha__gte=mes_actual).aggregate(
        total_litros=Sum('litros'), total_monto=Sum('monto')
    )
    gasto_peajes_mes = GastoPeaje.objects.filter(fecha__gte=mes_actual).aggregate(total_monto=Sum('monto'))
    costos_viaje_mes = CostoViaje.objects.filter(fecha__gte=mes_actual).aggregate(
        total_combustible=Sum('total_combustible'), total_peajes=Sum('total_peajes'),
        total_mantencion=Sum('total_mantencion'), total_km=Sum('km_recorridos'), total_costo=Sum('costo_total')
    )
    
    ranking_combustible = GastoCombustible.objects.values('vehiculo__patente', 'vehiculo__marca', 'vehiculo__modelo').annotate(
        total_litros=Sum('litros'), total_monto=Sum('monto')
    ).order_by('-total_monto')[:10]
    
    ranking_peajes = GastoPeaje.objects.values('vehiculo__patente', 'vehiculo__marca', 'vehiculo__modelo').annotate(
        total_monto=Sum('monto')
    ).order_by('-total_monto')[:10]
    
    ranking_costos_viaje = CostoViaje.objects.values('vehiculo__patente', 'vehiculo__marca', 'vehiculo__modelo').annotate(
        total_costo=Sum('costo_total'), total_km=Sum('km_recorridos'), cantidad_viajes=Count('id')
    ).order_by('-total_costo')[:10]
    
    ranking_conductores = CostoViaje.objects.values('conductor__id', 'conductor__nombres', 'conductor__apellidos').annotate(
        total_costo=Sum('costo_total'), total_km=Sum('km_recorridos'), cantidad_viajes=Count('id')
    ).order_by('-total_costo')[:10]
    
    context = {
        'gasto_combustible_mes': {
            'litros': gasto_combustible_mes.get('total_litros') or 0,
            'monto': gasto_combustible_mes.get('total_monto') or 0,
        },
        'gasto_peajes_mes': gasto_peajes_mes.get('total_monto') or 0,
        'costos_viaje_mes': {
            'combustible': costos_viaje_mes.get('total_combustible') or 0,
            'peajes': costos_viaje_mes.get('total_peajes') or 0,
            'mantencion': costos_viaje_mes.get('total_mantencion') or 0,
            'km': costos_viaje_mes.get('total_km') or 0,
            'total': costos_viaje_mes.get('total_costo') or 0,
        },
        'ranking_combustible': ranking_combustible,
        'ranking_peajes': ranking_peajes,
        'ranking_costos_viaje': ranking_costos_viaje,
        'ranking_conductores': ranking_conductores,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_passes_test(es_administrador)
def lista_gastos(request):
    """Lista todos los gastos de combustible"""
    gastos = GastoCombustible.objects.all().order_by('-fecha')
    total_litros = gastos.aggregate(total=Sum('litros'))['total'] or 0
    total_monto = gastos.aggregate(total=Sum('monto'))['total'] or 0
    
    context = {
        'gastos': gastos,
        'total_litros': total_litros,
        'total_monto': total_monto,
    }
    return render(request, 'analytics/lista_gastos.html', context)


@login_required
@user_passes_test(es_administrador)
def cargar_combustible(request):
    if request.method == 'POST':
        form = GastoCombustibleForm(request.POST)
        if form.is_valid():
            gasto = form.save()
            messages.success(request, f'Gasto de combustible registrado: {gasto.litros}L - ${gasto.monto}')
            return redirect('analytics:lista_gastos')
    else:
        # Obtener último kilometraje del vehículo seleccionado
        vehiculo_id = request.GET.get('vehiculo')
        ultimo_km = None
        if vehiculo_id:
            ultimo_gasto = GastoCombustible.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha').first()
            if ultimo_gasto:
                ultimo_km = ultimo_gasto.kilometraje
        
        form = GastoCombustibleForm(initial={'vehiculo': vehiculo_id})
    
    return render(request, 'analytics/cargar_combustible.html', {
        'form': form, 
        'titulo': 'Cargar Combustible'
    })


@login_required
@user_passes_test(es_administrador)
def cargar_peaje(request):
    if request.method == 'POST':
        form = GastoPeajeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto de peaje registrado correctamente.')
            return redirect('analytics:dashboard')
    else:
        form = GastoPeajeForm()
    
    return render(request, 'analytics/cargar_peaje.html', {'form': form, 'titulo': 'Cargar Peaje'})


@login_required
@user_passes_test(es_administrador)
def cargar_costo_viaje(request):
    if request.method == 'POST':
        form = CostoViajeForm(request.POST)
        if form.is_valid():
            costo = form.save(commit=False)
            costo.calcular_costo_total()
            costo.save()
            messages.success(request, 'Costo de viaje registrado correctamente.')
            return redirect('analytics:dashboard')
    else:
        form = CostoViajeForm()
    
    return render(request, 'analytics/cargar_costo_viaje.html', {'form': form, 'titulo': 'Cargar Costo de Viaje'})


@login_required
@user_passes_test(es_administrador)
def api_ultimo_kilometraje(request, vehiculo_id):
    """API para obtener el último kilometraje del vehículo"""
    ultimo_gasto = GastoCombustible.objects.filter(vehiculo_id=vehiculo_id).order_by('-fecha').first()
    return JsonResponse({
        'ultimo_km': ultimo_gasto.kilometraje if ultimo_gasto else None,
        'ultima_fecha': ultimo_gasto.fecha.strftime('%d/%m/%Y') if ultimo_gasto else None
    })