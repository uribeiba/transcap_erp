# En la parte superior de views.py, las importaciones deben ser:
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta

from django.db.models import Sum, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.contrib.admin.views.decorators import staff_member_required

from remuneraciones.models import Liquidacion, LiquidacionDetalle, Empleado, Contrato, AFP, Salud, Concepto, Honorario
from remuneraciones.services.calculo_remuneraciones import CalculadoraRemuneraciones
from remuneraciones.services.liquidacion_service import LiquidacionService
from remuneraciones.services.sii_integration import SIIExporter
from remuneraciones.services.reportes_service import ReportesService  # ← Esta línea

# ============================================================
# VISTAS BASE (HTML)
# ============================================================

def dashboard(request):
    """Vista principal del módulo de remuneraciones."""
    return render(request, 'remuneraciones/dashboard.html')


def empleados(request):
    """Vista para gestión de empleados."""
    return render(request, 'remuneraciones/empleados.html')


def contratos(request):
    """Vista para gestión de contratos."""
    return render(request, 'remuneraciones/contratos.html')


def liquidaciones(request):
    """Vista principal de liquidaciones."""
    return render(request, 'remuneraciones/liquidaciones.html')


def honorarios(request):
    """Vista para gestión de honorarios."""
    return render(request, 'remuneraciones/honorarios.html')


def parametros(request):
    """Vista para configuración de parámetros (AFP, Salud, Conceptos)."""
    return render(request, 'remuneraciones/parametros.html')


# ============================================================
# API: CÁLCULO DE LIQUIDACIÓN (SIN GUARDAR)
# ============================================================

@require_GET
def calcular_liquidacion(request, contrato_id):
    """Endpoint para calcular liquidación SIN guardar en BD."""
    contrato = get_object_or_404(Contrato, id=contrato_id)

    bonos = request.GET.get('bonos', '0')
    horas_extra = request.GET.get('horas_extra', '0')

    try:
        bonos = Decimal(bonos)
        horas_extra = Decimal(horas_extra)
    except InvalidOperation:
        return JsonResponse({
            "error": "Parámetros inválidos: bonos y horas_extra deben ser numéricos"
        }, status=400)

    calc = CalculadoraRemuneraciones(contrato)
    resultado = calc.calcular(bonos=bonos, horas_extra=horas_extra)

    resultado_json = {
        k: float(v) if isinstance(v, Decimal) else v 
        for k, v in resultado.items()
    }

    return JsonResponse(resultado_json)


# ============================================================
# API: GUARDAR LIQUIDACIÓN INDIVIDUAL
# ============================================================

@csrf_exempt
@require_POST
def guardar_liquidacion(request, contrato_id):
    """Endpoint para guardar una liquidación en base de datos."""
    contrato = get_object_or_404(Contrato, id=contrato_id)

    bonos = request.POST.get('bonos', '0')
    horas_extra = request.POST.get('horas_extra', '0')
    periodo = request.POST.get('periodo')

    if not periodo:
        return JsonResponse({"error": "Parámetro 'periodo' requerido (formato YYYY-MM)"}, status=400)

    if len(periodo) != 7 or periodo[4] != '-':
        return JsonResponse({"error": "Formato de periodo inválido. Use YYYY-MM (ej: 2026-04)"}, status=400)

    try:
        bonos = Decimal(bonos)
        horas_extra = Decimal(horas_extra)
    except InvalidOperation:
        return JsonResponse({
            "error": "Parámetros inválidos: bonos y horas_extra deben ser numéricos"
        }, status=400)

    try:
        liquidacion = LiquidacionService.crear_liquidacion(
            empleado=contrato.empleado,
            contrato=contrato,
            periodo=periodo,
            bonos=bonos,
            horas_extra=horas_extra
        )
    except Exception as e:
        return JsonResponse({"error": f"No se pudo crear la liquidación: {str(e)}"}, status=500)

    return JsonResponse({
        "success": True,
        "liquidacion_id": liquidacion.id,
        "mensaje": "Liquidación creada correctamente"
    })


# ============================================================
# API: GENERAR LIQUIDACIONES MASIVAS
# ============================================================

@csrf_exempt
@require_POST
def generar_liquidaciones_periodo(request):
    """Endpoint para generar liquidaciones masivas para todos los contratos activos."""
    periodo = request.POST.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Parámetro 'periodo' requerido"}, status=400)

    bonos_generales = request.POST.get('bonos_generales', '0')
    horas_extra_generales = request.POST.get('horas_extra_generales', '0')

    try:
        bonos_generales = Decimal(bonos_generales)
        horas_extra_generales = Decimal(horas_extra_generales)
    except InvalidOperation:
        return JsonResponse({
            "error": "Parámetros inválidos: bonos_generales y horas_extra_generales deben ser numéricos"
        }, status=400)

    contratos = Contrato.objects.filter(activo=True).select_related('empleado')
    
    resumen = []
    errores = []

    for contrato in contratos:
        try:
            liquidacion = LiquidacionService.crear_liquidacion(
                empleado=contrato.empleado,
                contrato=contrato,
                periodo=periodo,
                bonos=bonos_generales,
                horas_extra=horas_extra_generales
            )
            resumen.append({
                "empleado": contrato.empleado.nombre_completo,
                "contrato_id": contrato.id,
                "liquidacion_id": liquidacion.id,
                "liquido_pagar": float(liquidacion.liquido_pagar)
            })
        except Exception as e:
            errores.append({
                "empleado": contrato.empleado.nombre_completo,
                "contrato_id": contrato.id,
                "error": str(e)
            })

    return JsonResponse({
        "success": True,
        "periodo": periodo,
        "total_procesados": len(contratos),
        "liquidaciones_creadas": resumen,
        "errores": errores
    })


# ============================================================
# API: RESUMEN MENSUAL DE LIQUIDACIONES
# ============================================================

@require_GET
def resumen_mensual(request):
    """Endpoint para obtener resumen contable de un período."""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Parámetro 'periodo' requerido (formato YYYY-MM)"}, status=400)

    liquidaciones = Liquidacion.objects.filter(periodo=periodo)
    if not liquidaciones.exists():
        return JsonResponse({"error": f"No hay liquidaciones para el periodo {periodo}"}, status=404)

    total_haberes = liquidaciones.aggregate(Sum('total_haberes'))['total_haberes__sum'] or 0
    total_descuentos = liquidaciones.aggregate(Sum('total_descuentos'))['total_descuentos__sum'] or 0
    total_liquido = liquidaciones.aggregate(Sum('liquido_pagar'))['liquido_pagar__sum'] or 0

    detalles = LiquidacionDetalle.objects.filter(
        liquidacion__periodo=periodo
    ).select_related('concepto')
    
    resumen_conceptos = {}
    for detalle in detalles:
        codigo = detalle.concepto.codigo
        if codigo not in resumen_conceptos:
            resumen_conceptos[codigo] = {
                "nombre": detalle.concepto.nombre,
                "tipo": detalle.concepto.tipo,
                "total": 0
            }
        resumen_conceptos[codigo]["total"] += float(detalle.monto)

    return JsonResponse({
        "periodo": periodo,
        "totales_generales": {
            "total_haberes": float(total_haberes),
            "total_descuentos": float(total_descuentos),
            "total_liquido": float(total_liquido)
        },
        "totales_por_concepto": resumen_conceptos
    })


# ============================================================
# VISTA: DETALLE DE LIQUIDACIÓN (HTML)
# ============================================================

def detalle_liquidacion(request, liquidacion_id):
    """Vista para mostrar el detalle completo de una liquidación."""
    liquidacion = get_object_or_404(Liquidacion, id=liquidacion_id)
    detalles = LiquidacionDetalle.objects.filter(
        liquidacion=liquidacion
    ).select_related('concepto')
    
    return render(request, 'remuneraciones/detalle_liquidacion.html', {
        'liquidacion': liquidacion,
        'detalles': detalles
    })


# ============================================================
# API: EXPORTACIÓN SII
# ============================================================

def exportar_dj1847(request):
    """Endpoint para exportar archivo DJ 1847 (Declaración de Honorarios)."""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido (formato YYYY-MM)"}, status=400)
    
    rut_empresa = "76.123.456-7"
    razon_social = "TRANSPORTES XYZ LIMITADA"
    
    archivo = SIIExporter.generar_dj1847(periodo, rut_empresa, razon_social)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    response = HttpResponse(contenido, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{archivo}"'
    return response


def exportar_dj1879(request):
    """Endpoint para exportar archivo DJ 1879 (Detalle de Liquidaciones)."""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido (formato YYYY-MM)"}, status=400)
    
    rut_empresa = "76.123.456-7"
    razon_social = "TRANSPORTES XYZ LIMITADA"
    
    archivo = SIIExporter.generar_dj1879(periodo, rut_empresa, razon_social)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    response = HttpResponse(contenido, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{archivo}"'
    return response


# ============================================================
# API: DASHBOARD
# ============================================================

def dashboard_stats(request):
    """Estadísticas para el dashboard."""
    ahora = datetime.now()
    periodo_actual = ahora.strftime('%Y-%m')
    
    stats = {
        'total_empleados': Empleado.objects.filter(activo=True).count(),
        'total_contratos': Contrato.objects.filter(activo=True).count(),
        'masa_salarial': float(Contrato.objects.aggregate(total=Sum('sueldo_base'))['total'] or 0),
        'liquido_mes_actual': float(Liquidacion.objects.filter(periodo=periodo_actual).aggregate(total=Sum('liquido_pagar'))['total'] or 0)
    }
    
    return JsonResponse(stats)


def dashboard_evolucion(request):
    """Evolución de últimos 6 meses."""
    meses = []
    liquidos = []
    
    for i in range(5, -1, -1):
        fecha = datetime.now() - timedelta(days=30*i)
        periodo = fecha.strftime('%Y-%m')
        meses.append(periodo)
        
        total = Liquidacion.objects.filter(periodo=periodo).aggregate(total=Sum('liquido_pagar'))['total'] or 0
        liquidos.append(float(total))
    
    return JsonResponse({
        'periodos': meses,
        'liquidos': liquidos
    })


def dashboard_conceptos(request):
    """Distribución de conceptos para un período."""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido"}, status=400)
    
    conceptos = LiquidacionDetalle.objects.filter(
        liquidacion__periodo=periodo
    ).values('concepto__nombre').annotate(
        total=Sum('monto')
    ).order_by('-total')[:5]
    
    return JsonResponse({
        'labels': [c['concepto__nombre'] for c in conceptos],
        'data': [float(c['total']) for c in conceptos]
    })


def dashboard_ultimas_liquidaciones(request):
    """Últimas 10 liquidaciones."""
    liquidaciones = Liquidacion.objects.select_related('empleado').order_by('-periodo', '-id')[:10]
    
    data = [{
        'id': liq.id,
        'periodo': liq.periodo,
        'empleado': liq.empleado.nombre_completo,
        'total_haberes': float(liq.total_haberes),
        'total_descuentos': float(liq.total_descuentos),
        'liquido_pagar': float(liq.liquido_pagar)
    } for liq in liquidaciones]
    
    return JsonResponse(data, safe=False)


# ============================================================
# API: EMPLEADOS CRUD
# ============================================================

@csrf_exempt
def api_empleados_list(request):
    """CRUD de empleados."""
    import json
    
    if request.method == 'GET':
        empleados = Empleado.objects.all()
        data = [{
            'id': emp.id,
            'rut': emp.rut,
            'nombres': emp.nombres,
            'apellidos': emp.apellidos,
            'nombre_completo': emp.nombre_completo,
            'fecha_nacimiento': emp.fecha_nacimiento,
            'fecha_ingreso': emp.fecha_ingreso,
            'cargo': emp.cargo,
            'area': emp.area,
            'activo': emp.activo
        } for emp in empleados]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            empleado = Empleado.objects.create(
                rut=data['rut'],
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                fecha_nacimiento=data['fecha_nacimiento'],
                fecha_ingreso=data['fecha_ingreso'],
                tipo_contrato=data.get('tipo_contrato', 'INDEFINIDO'),
                cargo=data.get('cargo', ''),
                area=data.get('area', ''),
                activo=data.get('activo', True)
            )
            return JsonResponse({'id': empleado.id, 'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def api_empleado_detail(request, empleado_id):
    """Obtener o eliminar un empleado específico."""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'DELETE':
        empleado.delete()
        return JsonResponse({'success': True})
    
    data = {
        'id': empleado.id,
        'rut': empleado.rut,
        'nombres': empleado.nombres,
        'apellidos': empleado.apellidos,
        'fecha_nacimiento': empleado.fecha_nacimiento,
        'fecha_ingreso': empleado.fecha_ingreso,
        'cargo': empleado.cargo,
        'area': empleado.area,
        'activo': empleado.activo
    }
    return JsonResponse(data)


# ============================================================
# API: CONTRATOS CRUD
# ============================================================

@csrf_exempt
def api_contratos_list(request):
    """CRUD de contratos."""
    import json
    
    if request.method == 'GET':
        contratos = Contrato.objects.select_related('empleado', 'afp', 'salud').all()
        data = [{
            'id': c.id,
            'empleado_id': c.empleado.id,
            'empleado_nombre': c.empleado.nombre_completo,
            'empleado_rut': c.empleado.rut,
            'sueldo_base': float(c.sueldo_base),
            'fecha_inicio': c.fecha_inicio,
            'fecha_fin': c.fecha_fin,
            'tipo_jornada': c.tipo_jornada,
            'horas_semanales': c.horas_semanales,
            'afp_id': c.afp.id if c.afp else None,
            'afp_nombre': c.afp.nombre if c.afp else None,
            'salud_id': c.salud.id if c.salud else None,
            'salud_nombre': c.salud.nombre if c.salud else None,
            'activo': c.activo
        } for c in contratos]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        contrato = Contrato.objects.create(
            empleado_id=data['empleado_id'],
            sueldo_base=data['sueldo_base'],
            fecha_inicio=data['fecha_inicio'],
            fecha_fin=data.get('fecha_fin'),
            tipo_jornada=data['tipo_jornada'],
            horas_semanales=data.get('horas_semanales', 45),
            afp_id=data.get('afp_id'),
            salud_id=data.get('salud_id'),
            activo=data.get('activo', True)
        )
        return JsonResponse({'id': contrato.id})
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        contrato = Contrato.objects.get(id=data['id'])
        contrato.empleado_id = data['empleado_id']
        contrato.sueldo_base = data['sueldo_base']
        contrato.fecha_inicio = data['fecha_inicio']
        contrato.fecha_fin = data.get('fecha_fin')
        contrato.tipo_jornada = data['tipo_jornada']
        contrato.horas_semanales = data.get('horas_semanales', 45)
        contrato.afp_id = data.get('afp_id')
        contrato.salud_id = data.get('salud_id')
        contrato.activo = data.get('activo', True)
        contrato.save()
        return JsonResponse({'success': True})


def api_contrato_detail(request, contrato_id):
    """Obtener o eliminar un contrato específico."""
    contrato = get_object_or_404(Contrato, id=contrato_id)
    
    if request.method == 'DELETE':
        contrato.delete()
        return JsonResponse({'success': True})
    
    data = {
        'id': contrato.id,
        'empleado_id': contrato.empleado.id,
        'sueldo_base': float(contrato.sueldo_base),
        'fecha_inicio': contrato.fecha_inicio,
        'fecha_fin': contrato.fecha_fin,
        'tipo_jornada': contrato.tipo_jornada,
        'horas_semanales': contrato.horas_semanales,
        'afp_id': contrato.afp.id if contrato.afp else None,
        'salud_id': contrato.salud.id if contrato.salud else None,
        'activo': contrato.activo
    }
    return JsonResponse(data)


# ============================================================
# API: HONORARIOS CRUD
# ============================================================

@csrf_exempt
def api_honorarios_list(request):
    """CRUD de honorarios."""
    import json
    
    if request.method == 'GET':
        honorarios = Honorario.objects.all().order_by('-periodo', '-id')
        data = [{
            'id': h.id,
            'periodo': h.periodo,
            'rut_beneficiario': h.rut_beneficiario,
            'nombre_beneficiario': h.nombre_beneficiario,
            'monto_bruto': float(h.monto_bruto),
            'monto_retencion': float(h.monto_retencion),
            'monto_liquido': float(h.monto_liquido),
            'estado': h.estado
        } for h in honorarios]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        honorario = Honorario.objects.create(
            periodo=data['periodo'],
            rut_beneficiario=data['rut_beneficiario'],
            nombre_beneficiario=data['nombre_beneficiario'],
            monto_bruto=data['monto_bruto'],
            monto_retencion=data['monto_retencion'],
            monto_liquido=data['monto_liquido'],
            estado=data.get('estado', 'BORRADOR')
        )
        return JsonResponse({'id': honorario.id})
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        honorario = Honorario.objects.get(id=data['id'])
        honorario.periodo = data['periodo']
        honorario.rut_beneficiario = data['rut_beneficiario']
        honorario.nombre_beneficiario = data['nombre_beneficiario']
        honorario.monto_bruto = data['monto_bruto']
        honorario.monto_retencion = data['monto_retencion']
        honorario.monto_liquido = data['monto_liquido']
        honorario.estado = data.get('estado', 'BORRADOR')
        honorario.save()
        return JsonResponse({'success': True})


def api_honorario_detail(request, honorario_id):
    """Obtener o eliminar un honorario específico."""
    honorario = get_object_or_404(Honorario, id=honorario_id)
    
    if request.method == 'DELETE':
        honorario.delete()
        return JsonResponse({'success': True})
    
    data = {
        'id': honorario.id,
        'periodo': honorario.periodo,
        'rut_beneficiario': honorario.rut_beneficiario,
        'nombre_beneficiario': honorario.nombre_beneficiario,
        'monto_bruto': float(honorario.monto_bruto),
        'monto_retencion': float(honorario.monto_retencion),
        'monto_liquido': float(honorario.monto_liquido),
        'estado': honorario.estado
    }
    return JsonResponse(data)


# ============================================================
# API: LIQUIDACIONES LISTADO
# ============================================================

def api_liquidaciones_list(request):
    """Listar todas las liquidaciones."""
    liquidaciones = Liquidacion.objects.select_related('empleado', 'contrato').all().order_by('-periodo', '-id')
    
    data = [{
        'id': liq.id,
        'periodo': liq.periodo,
        'empleado_nombre': liq.empleado.nombre_completo,
        'empleado_rut': liq.empleado.rut,
        'total_haberes': float(liq.total_haberes),
        'total_descuentos': float(liq.total_descuentos),
        'liquido_pagar': float(liq.liquido_pagar),
        'fecha_pago': liq.fecha_pago,
        'created_at': liq.created_at
    } for liq in liquidaciones]
    
    return JsonResponse(data, safe=False)


# ============================================================
# API: AFP CRUD COMPLETO
# ============================================================

@csrf_exempt
def api_afp_list(request):
    """CRUD completo de AFP."""
    import json
    
    if request.method == 'GET':
        afps = AFP.objects.all()
        data = [{
            'id': a.id,
            'codigo': a.codigo,
            'nombre': a.nombre,
            'tasa_cotizacion': float(a.tasa_cotizacion),
            'comision': float(a.comision),
            'comision_adicional': float(a.comision_adicional) if hasattr(a, 'comision_adicional') else 0,
            'seguro_invalidez': float(a.seguro_invalidez) if hasattr(a, 'seguro_invalidez') else 0.0144,
            'activo': a.activo
        } for a in afps]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        afp = AFP.objects.create(
            codigo=data['codigo'],
            nombre=data['nombre'],
            tasa_cotizacion=data['tasa_cotizacion'],
            comision=data['comision'],
            seguro_invalidez=data.get('seguro_invalidez', 0.0144),
            activo=data.get('activo', True)
        )
        return JsonResponse({'id': afp.id})


def api_afp_detail(request, afp_id):
    """Obtener o eliminar una AFP específica."""
    afp = get_object_or_404(AFP, id=afp_id)
    
    if request.method == 'DELETE':
        afp.delete()
        return JsonResponse({'success': True})
    
    data = {
        'id': afp.id,
        'codigo': afp.codigo,
        'nombre': afp.nombre,
        'tasa_cotizacion': float(afp.tasa_cotizacion),
        'comision': float(afp.comision),
        'comision_adicional': float(afp.comision_adicional) if hasattr(afp, 'comision_adicional') else 0,
        'seguro_invalidez': float(afp.seguro_invalidez) if hasattr(afp, 'seguro_invalidez') else 0.0144,
        'activo': afp.activo
    }
    return JsonResponse(data)


# ============================================================
# API: SALUD CRUD COMPLETO
# ============================================================

@csrf_exempt
def api_salud_list(request):
    """CRUD completo de Salud (Fonasa/Isapre)."""
    import json
    
    if request.method == 'GET':
        salud_list = Salud.objects.all()
        data = [{
            'id': s.id,
            'nombre': s.nombre,
            'codigo': s.codigo,
            'tipo': s.tipo,
            'plan': s.plan if hasattr(s, 'plan') else 'BASE',
            'tasa_cotizacion': float(s.tasa_cotizacion),
            'tasa_adicional': float(s.tasa_adicional) if hasattr(s, 'tasa_adicional') else 0,
            'monto_adicional': float(s.monto_adicional) if hasattr(s, 'monto_adicional') else 0,
            'activo': s.activo
        } for s in salud_list]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        salud = Salud.objects.create(
            nombre=data['nombre'],
            codigo=data.get('codigo'),
            tipo=data['tipo'],
            plan=data.get('plan', 'BASE'),
            tasa_cotizacion=data['tasa_cotizacion'],
            tasa_adicional=data.get('tasa_adicional', 0),
            monto_adicional=data.get('monto_adicional', 0),
            activo=data.get('activo', True)
        )
        return JsonResponse({'id': salud.id})


def api_salud_detail(request, salud_id):
    """Obtener o eliminar una institución de salud específica."""
    salud = get_object_or_404(Salud, id=salud_id)
    
    if request.method == 'DELETE':
        salud.delete()
        return JsonResponse({'success': True})
    
    data = {
        'id': salud.id,
        'nombre': salud.nombre,
        'codigo': salud.codigo,
        'tipo': salud.tipo,
        'plan': salud.plan if hasattr(salud, 'plan') else 'BASE',
        'tasa_cotizacion': float(salud.tasa_cotizacion),
        'tasa_adicional': float(salud.tasa_adicional) if hasattr(salud, 'tasa_adicional') else 0,
        'monto_adicional': float(salud.monto_adicional) if hasattr(salud, 'monto_adicional') else 0,
        'activo': salud.activo
    }
    return JsonResponse(data)


# ============================================================
# API: CONCEPTOS CRUD COMPLETO
# ============================================================

@csrf_exempt
def api_conceptos_list(request):
    """CRUD completo de Conceptos (Haberes y Descuentos)."""
    import json
    
    if request.method == 'GET':
        tipo = request.GET.get('tipo', '')
        if tipo:
            tipos = tipo.split(',')
            conceptos = Concepto.objects.filter(tipo__in=tipos, activo=True)
        else:
            conceptos = Concepto.objects.all()
        
        data = [{
            'id': c.id,
            'codigo': c.codigo,
            'nombre': c.nombre,
            'tipo': c.tipo,
            'categoria': c.categoria,
            'es_imponible': c.es_imponible,
            'es_tributable': c.es_tributable,
            'monto_fijo': float(c.monto_fijo) if c.monto_fijo else None,
            'porcentaje': float(c.porcentaje) if c.porcentaje else None,
            'formula': c.formula,
            'orden': c.orden,
            'activo': c.activo
        } for c in conceptos]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        concepto = Concepto.objects.create(
            codigo=data['codigo'],
            nombre=data['nombre'],
            tipo=data['tipo'],
            categoria=data.get('categoria'),
            es_imponible=data.get('es_imponible', True),
            es_tributable=data.get('es_tributable', True),
            monto_fijo=data.get('monto_fijo'),
            porcentaje=data.get('porcentaje'),
            formula=data.get('formula'),
            orden=data.get('orden', 0),
            activo=data.get('activo', True)
        )
        return JsonResponse({'id': concepto.id})
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        concepto = Concepto.objects.get(id=data['id'])
        concepto.codigo = data['codigo']
        concepto.nombre = data['nombre']
        concepto.tipo = data['tipo']
        concepto.categoria = data.get('categoria')
        concepto.es_imponible = data.get('es_imponible', True)
        concepto.es_tributable = data.get('es_tributable', True)
        concepto.monto_fijo = data.get('monto_fijo')
        concepto.porcentaje = data.get('porcentaje')
        concepto.formula = data.get('formula')
        concepto.orden = data.get('orden', 0)
        concepto.activo = data.get('activo', True)
        concepto.save()
        return JsonResponse({'success': True})


def api_concepto_detail(request, concepto_id):
    """Obtener o eliminar un concepto específico."""
    concepto = get_object_or_404(Concepto, id=concepto_id)
    
    if request.method == 'DELETE':
        concepto.delete()
        return JsonResponse({'success': True})
    
    data = {
        'id': concepto.id,
        'codigo': concepto.codigo,
        'nombre': concepto.nombre,
        'tipo': concepto.tipo,
        'categoria': concepto.categoria,
        'es_imponible': concepto.es_imponible,
        'es_tributable': concepto.es_tributable,
        'monto_fijo': float(concepto.monto_fijo) if concepto.monto_fijo else None,
        'porcentaje': float(concepto.porcentaje) if concepto.porcentaje else None,
        'formula': concepto.formula,
        'orden': concepto.orden,
        'activo': concepto.activo
    }
    return JsonResponse(data)


# ============================================================
# API: EDITAR LIQUIDACIÓN (SOLO ADMINISTRADORES)
# ============================================================


@staff_member_required
def editar_liquidacion(request, liquidacion_id):
    """
    Endpoint para editar una liquidación existente.
    SOLO ACCESIBLE PARA ADMINISTRADORES (staff).
    
    POST params:
        - bonos (Decimal): Bonos adicionales
        - horas_extra (Decimal): Horas extra
        - periodo (string, opcional): Nuevo período
    """
    from decimal import Decimal
    from remuneraciones.models import LiquidacionDetalle, Concepto
    
    liquidacion = get_object_or_404(Liquidacion, id=liquidacion_id)
    
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    bonos = request.POST.get('bonos', '0')
    horas_extra = request.POST.get('horas_extra', '0')
    periodo = request.POST.get('periodo')
    
    try:
        bonos = Decimal(bonos)
        horas_extra = Decimal(horas_extra)
    except InvalidOperation:
        return JsonResponse({"error": "Parámetros inválidos"}, status=400)
    
    # Recalcular con nuevos valores
    calc = CalculadoraRemuneraciones(liquidacion.contrato)
    resultado = calc.calcular(bonos=bonos, horas_extra=horas_extra)
    
    # Actualizar liquidación
    if periodo:
        liquidacion.periodo = periodo
    liquidacion.total_haberes = resultado['imponible']
    liquidacion.total_descuentos = resultado['afp'] + resultado['salud'] + resultado['afc'] + resultado['impuesto']
    liquidacion.liquido_pagar = resultado['liquido']
    liquidacion.save()
    
    # Actualizar detalles (eliminar y recrear)
    liquidacion.detalles.all().delete()
    
    def add_detalle(codigo, nombre, tipo, monto):
        concepto, _ = Concepto.objects.get_or_create(
            codigo=codigo, 
            defaults={'nombre': nombre, 'tipo': tipo}
        )
        LiquidacionDetalle.objects.create(
            liquidacion=liquidacion, 
            concepto=concepto, 
            monto=monto
        )
    
    add_detalle("SUELDO_BASE", "Sueldo Base", "HABER_IMPONIBLE", resultado['sueldo_base'])
    add_detalle("HORAS_EXTRA", "Horas Extra", "HABER_IMPONIBLE", resultado['horas_extra'])
    add_detalle("GRATIFICACION", "Gratificación", "HABER_IMPONIBLE", resultado['gratificacion'])
    add_detalle("AFP", "AFP", "DESCUENTO", resultado['afp'])
    add_detalle("SALUD", "Salud", "DESCUENTO", resultado['salud'])
    add_detalle("AFC", "AFC", "DESCUENTO", resultado['afc'])
    add_detalle("IMPUESTO", "Impuesto Único", "DESCUENTO", resultado['impuesto'])
    
    return JsonResponse({
        "success": True,
        "mensaje": "Liquidación actualizada correctamente",
        "liquidacion_id": liquidacion.id,
        "liquido_pagar": float(liquidacion.liquido_pagar)
    })


@staff_member_required
def eliminar_liquidacion(request, liquidacion_id):
    """
    Endpoint para eliminar una liquidación.
    SOLO ACCESIBLE PARA ADMINISTRADORES (staff).
    """
    liquidacion = get_object_or_404(Liquidacion, id=liquidacion_id)
    liquidacion.delete()
    
    return JsonResponse({
        "success": True,
        "mensaje": "Liquidación eliminada correctamente"
    })

@staff_member_required
def liquidaciones_administrar(request):
    """
    Vista de administración de liquidaciones (solo para staff).
    Muestra todas las liquidaciones con opciones de edición.
    """
    if not request.user.is_staff:
        return redirect('remuneraciones:dashboard')
    
    liquidaciones = Liquidacion.objects.select_related('empleado', 'contrato').all().order_by('-periodo', '-id')
    
    return render(request, 'remuneraciones/admin_liquidaciones.html', {
        'liquidaciones': liquidaciones,
        'is_admin': True
    })


@staff_member_required
def editar_liquidacion(request, liquidacion_id):
    """
    Endpoint para editar una liquidación existente.
    SOLO ACCESIBLE PARA ADMINISTRADORES (staff).
    """
    from decimal import Decimal
    
    liquidacion = get_object_or_404(Liquidacion, id=liquidacion_id)
    
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    bonos = request.POST.get('bonos', '0')
    horas_extra = request.POST.get('horas_extra', '0')
    periodo = request.POST.get('periodo')
    
    try:
        bonos = Decimal(bonos)
        horas_extra = Decimal(horas_extra)
    except InvalidOperation:
        return JsonResponse({"error": "Parámetros inválidos"}, status=400)
    
    # Recalcular con nuevos valores
    calc = CalculadoraRemuneraciones(liquidacion.contrato)
    resultado = calc.calcular(bonos=bonos, horas_extra=horas_extra)
    
    # Actualizar liquidación
    if periodo:
        liquidacion.periodo = periodo
    liquidacion.total_haberes = resultado['imponible']
    liquidacion.total_descuentos = resultado['afp'] + resultado['salud'] + resultado['afc'] + resultado['impuesto']
    liquidacion.liquido_pagar = resultado['liquido']
    liquidacion.save()
    
    # Actualizar detalles (eliminar y recrear)
    liquidacion.detalles.all().delete()
    
    from remuneraciones.models import Concepto
    
    def add_detalle(codigo, nombre, tipo, monto):
        concepto, _ = Concepto.objects.get_or_create(
            codigo=codigo, 
            defaults={'nombre': nombre, 'tipo': tipo}
        )
        from remuneraciones.models import LiquidacionDetalle
        LiquidacionDetalle.objects.create(
            liquidacion=liquidacion, 
            concepto=concepto, 
            monto=monto
        )
    
    add_detalle("SUELDO_BASE", "Sueldo Base", "HABER_IMPONIBLE", resultado['sueldo_base'])
    add_detalle("HORAS_EXTRA", "Horas Extra", "HABER_IMPONIBLE", resultado['horas_extra'])
    add_detalle("GRATIFICACION", "Gratificación", "HABER_IMPONIBLE", resultado['gratificacion'])
    add_detalle("AFP", "AFP", "DESCUENTO", resultado['afp'])
    add_detalle("SALUD", "Salud", "DESCUENTO", resultado['salud'])
    add_detalle("AFC", "AFC", "DESCUENTO", resultado['afc'])
    add_detalle("IMPUESTO", "Impuesto Único", "DESCUENTO", resultado['impuesto'])
    
    return JsonResponse({
        "success": True,
        "mensaje": "Liquidación actualizada correctamente",
        "liquidacion_id": liquidacion.id,
        "liquido_pagar": float(liquidacion.liquido_pagar)
    })


@staff_member_required
def eliminar_liquidacion(request, liquidacion_id):
    """
    Endpoint para eliminar una liquidación.
    SOLO ACCESIBLE PARA ADMINISTRADORES (staff).
    """
    liquidacion = get_object_or_404(Liquidacion, id=liquidacion_id)
    liquidacion.delete()
    
    return JsonResponse({
        "success": True,
        "mensaje": "Liquidación eliminada correctamente"
    })
    
# ============================================================
# API: OBTENER DETALLE DE LIQUIDACIÓN ESPECÍFICA
# ============================================================

def api_liquidacion_detail(request, liquidacion_id):
    """
    Obtener detalles de una liquidación específica.
    """
    liquidacion = get_object_or_404(Liquidacion, id=liquidacion_id)
    
    data = {
        'id': liquidacion.id,
        'periodo': liquidacion.periodo,
        'empleado_nombre': liquidacion.empleado.nombre_completo,
        'empleado_rut': liquidacion.empleado.rut,
        'total_haberes': float(liquidacion.total_haberes),
        'total_descuentos': float(liquidacion.total_descuentos),
        'liquido_pagar': float(liquidacion.liquido_pagar),
        'contrato_id': liquidacion.contrato.id,
        'detalles': []
    }
    
    # Agregar detalles
    for detalle in liquidacion.detalles.select_related('concepto').all():
        data['detalles'].append({
            'concepto': detalle.concepto.nombre,
            'codigo': detalle.concepto.codigo,
            'monto': float(detalle.monto),
            'tipo': detalle.concepto.tipo
        })
    
    return JsonResponse(data)


# ============================================================
# REPORTES
# ============================================================



def reportes(request):
    """Vista principal de reportes"""
    return render(request, 'remuneraciones/reportes.html')


def generar_reporte_previred(request):
    """Genera archivo para Previred"""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido"}, status=400)
    
    rut_empresa = request.GET.get('rut_empresa', '76.123.456-7')
    razon_social = request.GET.get('razon_social', 'TRANSCAP SPA')
    
    archivo = ReportesService.generar_archivo_previred(periodo, rut_empresa, razon_social)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    response = HttpResponse(contenido, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{archivo}"'
    return response


def generar_libro_remuneraciones(request):
    """Genera libro de remuneraciones (CSV)"""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido"}, status=400)
    
    rut_empresa = request.GET.get('rut_empresa', '76.123.456-7')
    razon_social = request.GET.get('razon_social', 'TRANSCAP SPA')
    
    archivo = ReportesService.generar_libro_remuneraciones(periodo, rut_empresa, razon_social)
    
    with open(archivo, 'r', encoding='utf-8-sig') as f:
        contenido = f.read()
    
    response = HttpResponse(contenido, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{archivo}"'
    return response


def generar_cotizaciones_previred(request):
    """Genera archivo de cotizaciones para Previred"""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido"}, status=400)
    
    rut_empresa = request.GET.get('rut_empresa', '76.123.456-7')
    razon_social = request.GET.get('razon_social', 'TRANSCAP SPA')
    
    archivo = ReportesService.generar_cotizaciones_previred(periodo, rut_empresa, razon_social)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    response = HttpResponse(contenido, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{archivo}"'
    return response


def generar_anexo_sii(request):
    """Genera anexo SII"""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido"}, status=400)
    
    rut_empresa = request.GET.get('rut_empresa', '76.123.456-7')
    razon_social = request.GET.get('razon_social', 'TRANSCAP SPA')
    
    archivo = ReportesService.generar_anexo_sii(periodo, rut_empresa, razon_social)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    response = HttpResponse(contenido, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{archivo}"'
    return response


def generar_resumen_ejecutivo(request):
    """Genera resumen ejecutivo"""
    periodo = request.GET.get('periodo')
    if not periodo:
        return JsonResponse({"error": "Periodo requerido"}, status=400)
    
    rut_empresa = request.GET.get('rut_empresa', '76.123.456-7')
    razon_social = request.GET.get('razon_social', 'TRANSCAP SPA')
    
    archivo = ReportesService.generar_resumen_ejecutivo(periodo, rut_empresa, razon_social)
    
    if not archivo:
        return JsonResponse({"error": f"No hay datos para el período {periodo}"}, status=404)
    
    with open(archivo, 'r', encoding='utf-8-sig') as f:
        contenido = f.read()
    
    response = HttpResponse(contenido, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{archivo}"'
    return response