# ============================================
# Imports estándar de Python
# ============================================
from io import BytesIO
from decimal import Decimal
from datetime import date as date_cls

# ============================================
# Imports de Django
# ============================================
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.db.models import (
    Q, Sum, Count, Case, When, F, Value, 
    DecimalField, ExpressionWrapper, Max
)
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

# ============================================
# Librerías externas
# ============================================
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# ============================================
# Imports de la app local (taller)
# ============================================
from .models import (
    Taller,
    Mantenimiento,
    MultaConductor,
    DocumentoVehiculo,
    DocumentoConductor,
    RutaViaje,
    CoordinacionViaje,
    Vehiculo,   # <- solo Vehiculo, sin Remolque
    Conductor
)

from .forms import (
    VehiculoForm, ConductorForm, DocumentoVehiculoForm,
    DocumentoConductorForm, MantenimientoForm, RutaViajeForm,
    CoordinacionViajeForm
)
from django.http import JsonResponse
from django.db.models import Count
from django.http import HttpResponse

# ============================================
# VISTAS PARA VEHÍCULOS
# ============================================

def flota_lista(request):
    """Lista todos los vehículos registrados"""
    vehiculos = Vehiculo.objects.all()
    return render(request, "taller/flota_lista.html", {"vehiculos": vehiculos})


def vehiculo_crear(request):
    """Crea un nuevo vehículo"""
    if request.method == "POST":
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("taller_flota")
    else:
        form = VehiculoForm()
    return render(request, "taller/vehiculo_form.html", {"form": form, "modo": "Crear"})


def vehiculo_editar(request, pk):
    """Edita un vehículo existente"""
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            return redirect("taller_flota")
    else:
        form = VehiculoForm(instance=vehiculo)
    return render(
        request,
        "taller/vehiculo_form.html",
        {"form": form, "modo": "Editar", "vehiculo": vehiculo},
    )


# ============================================
# VISTAS PARA CONDUCTORES
# ============================================

def conductores_lista(request):
    """Lista todos los conductores"""
    conductores = Conductor.objects.all()
    return render(
        request, "taller/conductores_lista.html", {"conductores": conductores}
    )


def conductor_crear(request):
    """Crea un nuevo conductor"""
    if request.method == "POST":
        form = ConductorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("taller_conductores")
    else:
        form = ConductorForm()
    return render(
        request, "taller/conductor_form.html", {"form": form, "modo": "Crear"}
    )


def conductor_editar(request, pk):
    """Edita un conductor existente"""
    conductor = get_object_or_404(Conductor, pk=pk)
    if request.method == "POST":
        form = ConductorForm(request.POST, instance=conductor)
        if form.is_valid():
            form.save()
            return redirect("taller_conductores")
    else:
        form = ConductorForm(instance=conductor)
    return render(
        request,
        "taller/conductor_form.html",
        {"form": form, "modo": "Editar", "conductor": conductor},
    )


# ============================================
# VISTAS PARA MANTENIMIENTOS
# ============================================

def mantenimientos_lista(request):
    """Lista mantenimientos con filtros"""
    qs = Mantenimiento.objects.select_related("vehiculo", "taller").all()

    # Aplicar filtros
    vehiculo_id = request.GET.get("vehiculo")
    tipo = request.GET.get("tipo")
    estado = request.GET.get("estado")
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")

    if vehiculo_id:
        qs = qs.filter(vehiculo_id=vehiculo_id)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if estado:
        qs = qs.filter(estado=estado)
    if desde:
        qs = qs.filter(Q(fecha_programada__gte=desde) | Q(fecha_real__gte=desde))
    if hasta:
        qs = qs.filter(Q(fecha_programada__lte=hasta) | Q(fecha_real__lte=hasta))

    vehiculos = Vehiculo.objects.order_by("patente")

    ctx = {
        "mantenimientos": qs.order_by("-fecha_programada", "-fecha_real", "-id"),
        "vehiculos": vehiculos,
        "f": {
            "vehiculo": vehiculo_id or "",
            "tipo": tipo or "",
            "estado": estado or "",
            "desde": desde or "",
            "hasta": hasta or "",
        },
    }
    return render(request, "taller/mantenimientos_lista.html", ctx)


def mantenimiento_crear(request):
    """Crea un nuevo mantenimiento"""
    if request.method == "POST":
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            m = form.save()
            messages.success(request, "Mantenimiento creado.")
            return redirect("taller_mantenimientos")
    else:
        initial = {}
        v = request.GET.get("vehiculo")
        if v:
            initial["vehiculo"] = v
        form = MantenimientoForm(initial=initial)
    return render(request, "taller/mantenimiento_form.html", {"form": form, "modo": "Crear"})


def mantenimiento_editar(request, pk):
    """Edita un mantenimiento existente"""
    m = get_object_or_404(Mantenimiento, pk=pk)
    if request.method == "POST":
        form = MantenimientoForm(request.POST, instance=m)
        if form.is_valid():
            m = form.save()

            # Actualizar km del vehículo si se finaliza
            if m.estado == "FINALIZADO" and m.km_real and (not m.vehiculo.km_actual or m.km_real > m.vehiculo.km_actual):
                m.vehiculo.km_actual = m.km_real
                m.vehiculo.save(update_fields=["km_actual"])

            messages.success(request, "Mantenimiento actualizado.")
            return redirect("taller_mantenimientos")
    else:
        form = MantenimientoForm(instance=m)
    return render(request, "taller/mantenimiento_form.html", {"form": form, "modo": "Editar", "m": m})


def mantenimiento_cambiar_estado(request, pk, nuevo_estado):
    """Cambia el estado de un mantenimiento (acción rápida)"""
    m = get_object_or_404(Mantenimiento, pk=pk)
    if nuevo_estado not in ["PLANIFICADO", "EN_PROCESO", "FINALIZADO"]:
        messages.error(request, "Estado no válido.")
        return redirect("taller_mantenimientos")

    m.estado = nuevo_estado
    # Si finaliza y no tiene fecha_real, asignar hoy
    if nuevo_estado == "FINALIZADO" and not m.fecha_real:
        m.fecha_real = timezone.now().date()
    m.save()
    messages.success(request, f"Estado actualizado a {nuevo_estado}.")
    return redirect("taller_mantenimientos")


# ============================================
# WIDGETS PARA FORMULARIOS
# ============================================

class DateInput(forms.DateInput):
    input_type = "date"


# ============================================
# VISTAS PARA DOCUMENTOS
# ============================================

def _anotar_estado_documentos(qs, campo_fecha="fecha_vencimiento", dias_alerta=30):
    """Anota 'dias_restantes' y 'estado_flag' (0=vencido,1=por_vencer,2=vigente)."""
    hoy = timezone.now().date()
    docs = list(qs)
    for d in docs:
        fv = getattr(d, campo_fecha, None)
        if not fv:
            d.dias_restantes = None
            d.estado_flag = 2
        else:
            d.dias_restantes = (fv - hoy).days
            if d.dias_restantes < 0:
                d.estado_flag = 0  # vencido
            elif d.dias_restantes <= dias_alerta:
                d.estado_flag = 1  # por vencer
            else:
                d.estado_flag = 2  # vigente
    # Ordenar por criticidad y fecha
    docs.sort(key=lambda x: (x.estado_flag, getattr(x, campo_fecha) or hoy))
    return docs


# -------------------- Documentos de Vehículos --------------------

def documentos_vehiculo_lista(request):
    """Lista documentos de vehículos con filtros"""
    tipo = request.GET.get("tipo") or ""
    estado = request.GET.get("estado") or ""
    vehiculo_id = request.GET.get("vehiculo") or ""
    qs = DocumentoVehiculo.objects.select_related("vehiculo")

    if tipo:
        qs = qs.filter(tipo=tipo)
    if vehiculo_id:
        qs = qs.filter(vehiculo_id=vehiculo_id)

    docs = _anotar_estado_documentos(qs)

    if estado:
        mapa = {"vencido": 0, "por_vencer": 1, "vigente": 2}
        docs = [d for d in docs if d.estado_flag == mapa.get(estado, 2)]

    ctx = {
        "docs": docs,
        "vehiculos": Vehiculo.objects.order_by("patente"),
        "f": {"tipo": tipo, "estado": estado, "vehiculo": vehiculo_id},
    }
    return render(request, "taller/documentos_vehiculos_lista.html", ctx)


def documento_vehiculo_nuevo(request):
    """Crea un nuevo documento de vehículo"""
    if request.method == "POST":
        form = DocumentoVehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de vehículo creado.")
            return redirect("taller_docs_vehiculos")
    else:
        initial = {}
        v = request.GET.get("vehiculo")
        if v:
            initial["vehiculo"] = v
        form = DocumentoVehiculoForm(initial=initial)
    return render(request, "taller/documento_vehiculo_form.html", {"form": form, "modo": "Crear"})


def documento_vehiculo_editar(request, pk):
    """Edita un documento de vehículo existente"""
    doc = get_object_or_404(DocumentoVehiculo, pk=pk)
    if request.method == "POST":
        form = DocumentoVehiculoForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de vehículo actualizado.")
            return redirect("taller_docs_vehiculos")
    else:
        form = DocumentoVehiculoForm(instance=doc)
    return render(request, "taller/documento_vehiculo_form.html", {"form": form, "modo": "Editar", "doc": doc})


# -------------------- Documentos de Conductores --------------------

def documentos_conductor_lista(request):
    """Lista documentos de conductores con filtros"""
    tipo = request.GET.get("tipo") or ""
    estado = request.GET.get("estado") or ""
    conductor_id = request.GET.get("conductor") or ""
    qs = DocumentoConductor.objects.select_related("conductor")

    if tipo:
        qs = qs.filter(tipo=tipo)
    if conductor_id:
        qs = qs.filter(conductor_id=conductor_id)

    docs = _anotar_estado_documentos(qs)

    if estado:
        mapa = {"vencido": 0, "por_vencer": 1, "vigente": 2}
        docs = [d for d in docs if d.estado_flag == mapa.get(estado, 2)]

    ctx = {
        "docs": docs,
        "conductores": Conductor.objects.order_by("apellidos", "nombres"),
        "f": {"tipo": tipo, "estado": estado, "conductor": conductor_id},
    }
    return render(request, "taller/documentos_conductores_lista.html", ctx)


def documento_conductor_nuevo(request):
    """Crea un nuevo documento de conductor"""
    if request.method == "POST":
        form = DocumentoConductorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de conductor creado.")
            return redirect("taller_docs_conductores")
    else:
        initial = {}
        c = request.GET.get("conductor")
        if c:
            initial["conductor"] = c
        form = DocumentoConductorForm(initial=initial)
    return render(request, "taller/documento_conductor_form.html", {"form": form, "modo": "Crear"})


def documento_conductor_editar(request, pk):
    """Edita un documento de conductor existente"""
    doc = get_object_or_404(DocumentoConductor, pk=pk)
    if request.method == "POST":
        form = DocumentoConductorForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de conductor actualizado.")
            return redirect("taller_docs_conductores")
    else:
        form = DocumentoConductorForm(instance=doc)
    return render(request, "taller/documento_conductor_form.html", {"form": form, "modo": "Editar", "doc": doc})


# ============================================
# REPORTES DE VEHÍCULOS
# ============================================

def reporte_vehiculo_selector(request):
    """Selector de vehículos para reportes"""
    q = request.GET.get("q", "").strip()
    vehiculos = Vehiculo.objects.all().order_by("patente")
    if q:
        vehiculos = vehiculos.filter(patente__icontains=q)
    return render(request, "taller/reporte_vehiculo_selector.html", {"vehiculos": vehiculos, "q": q})


def _rango_ultimos_12_meses():
    """Genera rango de últimos 12 meses"""
    hoy = timezone.now().date().replace(day=1)
    meses = []
    y, m = hoy.year, hoy.month
    for _ in range(12):
        meses.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    meses.reverse()
    return meses


def reporte_vehiculo(request, vehiculo_id: int):
    """Reporte detallado de vehículo"""
    v = get_object_or_404(Vehiculo, pk=vehiculo_id)

    # Costos de mantenimiento últimos 12 meses
    costo_total_expr = ExpressionWrapper(
        Coalesce(F("costo_mano_obra"), 0) + Coalesce(F("costo_repuestos"), 0),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    agg = (
        Mantenimiento.objects.filter(vehiculo=v)
        .annotate(fecha_ref=Coalesce(F("fecha_real"), F("fecha_programada")))
        .annotate(mes=TruncMonth("fecha_ref"))
        .annotate(costo_total=costo_total_expr)
        .values("mes")
        .annotate(costo=Sum("costo_total"))
        .order_by("mes")
    )

    # Normalizar a últimos 12 meses
    mapa = {(a["mes"].year, a["mes"].month): float(a["costo"] or 0) for a in agg if a["mes"]}
    labels, data = [], []
    for y, m in _rango_ultimos_12_meses():
        labels.append(f"{m:02d}-{y}")
        data.append(mapa.get((y, m), 0))

    total_12m = sum(data)
    total_mantenimientos = Mantenimiento.objects.filter(vehiculo=v).count()

    # Documentos
    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)
    docs_qs = DocumentoVehiculo.objects.filter(vehiculo=v)
    docs_vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    docs_porvencer = docs_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite).count()
    docs_vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    # Próximo mantenimiento preventivo
    proximo_preventivo = (
        Mantenimiento.objects.filter(vehiculo=v, tipo="PREVENTIVO")
        .exclude(fecha_programada__isnull=True)
        .order_by("fecha_programada")
        .first()
    ) or (
        Mantenimiento.objects.filter(vehiculo=v, tipo="PREVENTIVO")
        .exclude(km_programado__isnull=True)
        .order_by("km_programado")
        .first()
    )

    ctx = {
        "vehiculo": v,
        "labels": labels,
        "data": data,
        "total_12m": total_12m,
        "total_mantenimientos": total_mantenimientos,
        "docs": {
            "vencidos": docs_vencidos,
            "por_vencer": docs_porvencer,
            "vigentes": docs_vigentes,
            "limite": limite,
        },
        "proximo_preventivo": proximo_preventivo,
    }
    return render(request, "taller/reporte_vehiculo.html", ctx)


def reporte_vehiculo_pdf(request, vehiculo_id: int):
    """Genera PDF del reporte de vehículo"""
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)

    # Cálculo de costos de mantenimiento
    costo_total_expr = ExpressionWrapper(
        Coalesce(F("costo_mano_obra"), 0) + Coalesce(F("costo_repuestos"), 0),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    base_qs = (
        Mantenimiento.objects.filter(vehiculo=vehiculo)
        .annotate(costo_total_calc=costo_total_expr)
    )

    mant_qs = (
        base_qs
        .annotate(fecha_ref=Coalesce(F("fecha_real"), F("fecha_programada")))
        .order_by("-fecha_ref")
    )

    total_mantenimientos = mant_qs.count()

    # Últimos 12 meses
    hace_12_meses = timezone.now().date() - timezone.timedelta(days=365)
    total_12m = float(
        base_qs.filter(
            Q(fecha_real__gte=hace_12_meses) | Q(fecha_programada__gte=hace_12_meses)
        ).aggregate(s=Sum("costo_total_calc"))["s"] or 0
    )

    # Datos para gráfico: últimos 6 meses
    hoy_1 = timezone.now().date().replace(day=1)
    y_cur, m_cur = hoy_1.year, hoy_1.month
    meses = []
    for _ in range(6):
        meses.append((y_cur, m_cur))
        m_cur -= 1
        if m_cur == 0:
            m_cur = 12
            y_cur -= 1
    meses = list(reversed(meses))

    first_year, first_month = meses[0]
    first_date = date_cls(first_year, first_month, 1)

    agg_mes = (
        base_qs
        .filter(Q(fecha_real__gte=first_date) | Q(fecha_programada__gte=first_date))
        .annotate(mes=TruncMonth(Coalesce("fecha_real", "fecha_programada")))
        .values("mes")
        .annotate(total=Sum("costo_total_calc"))
    )
    mapa_mes = {
        (a["mes"].year, a["mes"].month): float(a["total"] or 0)
        for a in agg_mes
        if a["mes"]
    }

    series_vals = [mapa_mes.get(key, 0) for key in meses]
    max_val = max(series_vals) if series_vals else 1.0

    # Documentos del vehículo
    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)
    docs_qs = DocumentoVehiculo.objects.filter(vehiculo=vehiculo).order_by("fecha_vencimiento")
    docs_vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    docs_porvencer = docs_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite).count()
    docs_vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    # Generar PDF
    response = HttpResponse(content_type="application/pdf")
    filename = f"reporte_vehiculo_{vehiculo.patente}.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    x = 20 * mm
    y = height - 20 * mm

    # Logo
    logo_path = finders.find("img/logo_transcap.png")
    title_x = x
    if logo_path:
        logo_w = 35 * mm
        logo_h = 15 * mm
        try:
            p.drawImage(logo_path, x, y - logo_h + 5 * mm, width=logo_w, height=logo_h, mask="auto")
            title_x = x + logo_w + 5 * mm
        except Exception:
            title_x = x

    # Encabezado
    p.setFont("Helvetica-Bold", 14)
    p.drawString(title_x, y, "Transcap ERP - Reporte de Vehículo")
    y -= 10 * mm

    p.setFont("Helvetica", 10)
    p.drawString(x, y, f"Fecha emisión: {hoy.strftime('%d/%m/%Y')}")
    y -= 10 * mm

    # Datos del vehículo
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Vehículo")
    y -= 6 * mm

    p.setFont("Helvetica", 10)
    p.drawString(x, y, f"Patente: {vehiculo.patente}")
    y -= 5 * mm
    p.drawString(x, y, f"Marca / Modelo: {vehiculo.marca} {vehiculo.modelo}")
    y -= 5 * mm
    if hasattr(vehiculo, "anio") and vehiculo.anio:
        p.drawString(x, y, f"Año: {vehiculo.anio}")
        y -= 5 * mm
    y -= 5 * mm

    # KPIs
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Resumen de mantenimiento")
    y -= 6 * mm

    p.setFont("Helvetica", 10)
    p.drawString(
        x,
        y,
        f"Costo mantenciones últimos 12 meses: ${int(total_12m):,}".replace(",", "."),
    )
    y -= 5 * mm
    p.drawString(x, y, f"Total mantenciones registradas: {total_mantenimientos}")
    y -= 5 * mm
    p.drawString(
        x,
        y,
        "Documentos vencidos/por vencer/vigentes: "
        f"{docs_vencidos}/{docs_porvencer}/{docs_vigentes}",
    )
    y -= 10 * mm

    # Gráfico de barras (últimos 6 meses)
    chart_height = 40 * mm
    chart_width = width - 40 * mm
    chart_left = x
    chart_bottom = y - chart_height

    p.setLineWidth(0.5)
    p.line(chart_left, chart_bottom, chart_left, chart_bottom + chart_height)
    p.line(chart_left, chart_bottom, chart_left + chart_width, chart_bottom)

    n = len(meses)
    if n > 0:
        gap = chart_width / (n * 2)
        bar_width = gap
        for idx, val in enumerate(series_vals):
            bar_x = chart_left + gap * (1 + 2 * idx)
            bar_h = (val / max_val) * (chart_height * 0.8)
            p.rect(bar_x, chart_bottom, bar_width, bar_h, stroke=1, fill=0)

            mes_label = f"{meses[idx][1]:02d}/{str(meses[idx][0])[-2:]}"
            p.setFont("Helvetica", 6)
            p.drawCentredString(bar_x + bar_width / 2, chart_bottom - 4 * mm, mes_label)

    p.setFont("Helvetica-Bold", 10)
    p.drawString(chart_left, chart_bottom + chart_height + 3 * mm, "Costo mantenciones últimos 6 meses")

    y = chart_bottom - 10 * mm

    # Tabla de últimos mantenimientos
    if y < 60 * mm:
        p.showPage()
        y = height - 20 * mm

    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Últimos mantenimientos")
    y -= 6 * mm

    col_fecha_prog = x
    col_fecha_real = x + 30 * mm
    col_tipo = x + 60 * mm
    col_costo = x + 105 * mm
    col_estado = x + 130 * mm

    p.setFont("Helvetica-Bold", 9)
    p.drawString(col_fecha_prog, y, "Fecha Prog.")
    p.drawString(col_fecha_real, y, "Fecha Real")
    p.drawString(col_tipo, y, "Tipo")
    p.drawString(col_costo, y, "Costo")
    p.drawString(col_estado, y, "Estado")
    y -= 4 * mm
    p.line(x, y + 2 * mm, width - 20 * mm, y + 2 * mm)
    y -= 2 * mm

    p.setFont("Helvetica", 8)

    def _nueva_pagina_mants(y_pos):
        p.showPage()
        new_y = height - 20 * mm
        p.setFont("Helvetica-Bold", 12)
        p.drawString(x, new_y, "Últimos mantenimientos (cont.)")
        new_y -= 6 * mm

        p.setFont("Helvetica-Bold", 9)
        p.drawString(col_fecha_prog, new_y, "Fecha Prog.")
        p.drawString(col_fecha_real, new_y, "Fecha Real")
        p.drawString(col_tipo, new_y, "Tipo")
        p.drawString(col_costo, new_y, "Costo")
        p.drawString(col_estado, new_y, "Estado")
        new_y -= 4 * mm
        p.line(x, new_y + 2 * mm, width - 20 * mm, new_y + 2 * mm)
        new_y -= 2 * mm
        p.setFont("Helvetica", 8)
        return new_y

    for m in mant_qs[:10]:
        if y < 30 * mm:
            y = _nueva_pagina_mants(y)

        fecha_prog = m.fecha_programada.strftime("%d/%m/%Y") if m.fecha_programada else "-"
        fecha_real = m.fecha_real.strftime("%d/%m/%Y") if m.fecha_real else "-"
        costo_total = int(getattr(m, "costo_total_calc", 0) or 0)
        costo_str = f"${costo_total:,}".replace(",", ".")
        tipo_txt = m.get_tipo_display() if hasattr(m, "get_tipo_display") else m.tipo
        estado_txt = m.get_estado_display() if hasattr(m, "get_estado_display") else getattr(m, "estado", "")

        p.drawString(col_fecha_prog, y, fecha_prog)
        p.drawString(col_fecha_real, y, fecha_real)
        p.drawString(col_tipo, y, tipo_txt[:20])
        p.drawRightString(col_costo + 20 * mm, y, costo_str)
        p.drawString(col_estado, y, estado_txt)
        y -= 4 * mm

        if m.descripcion:
            p.setFont("Helvetica-Oblique", 7)
            p.drawString(col_tipo, y, m.descripcion[:80])
            p.setFont("Helvetica", 8)
            y -= 4 * mm

    # Documentos del vehículo
    if y < 40 * mm:
        p.showPage()
        y = height - 20 * mm

    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Documentos del vehículo")
    y -= 6 * mm
    p.setFont("Helvetica", 9)

    for d in docs_qs:
        if y < 30 * mm:
            p.showPage()
            y = height - 20 * mm
            p.setFont("Helvetica-Bold", 12)
            p.drawString(x, y, "Documentos del vehículo (cont.)")
            y -= 6 * mm
            p.setFont("Helvetica", 9)

        tipo_doc = d.get_tipo_display() if hasattr(d, "get_tipo_display") else d.tipo
        emision = d.fecha_emision.strftime("%d/%m/%Y") if d.fecha_emision else "-"
        venc = d.fecha_vencimiento.strftime("%d/%m/%Y") if d.fecha_vencimiento else "-"

        if d.fecha_vencimiento and d.fecha_vencimiento < hoy:
            estado = "VENCIDO"
        elif d.fecha_vencimiento and d.fecha_vencimiento <= limite:
            estado = "POR VENCER"
        else:
            estado = "VIGENTE"

        p.drawString(x, y, f"- {tipo_doc}: {emision} → {venc}  ({estado})")
        y -= 4 * mm

    p.showPage()
    p.save()
    return response


# ============================================
# REPORTES DE CONDUCTORES
# ============================================

def reporte_conductor(request, conductor_id: int):
    """Reporte de documentos + multas por conductor"""
    conductor = get_object_or_404(Conductor, pk=conductor_id)

    # Documentos
    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)

    docs_qs = DocumentoConductor.objects.filter(conductor=conductor).order_by(
        "fecha_vencimiento"
    )

    vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    por_vencer = docs_qs.filter(
        fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite
    ).count()
    vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    # Multas
    multas_qs = MultaConductor.objects.filter(conductor=conductor).order_by(
        "-fecha", "-id"
    )

    total_multas = multas_qs.count()
    monto_total = float(
        multas_qs.aggregate(s=Sum("monto"))["s"] or 0
    )

    monto_pendiente = float(
        multas_qs.filter(estado="PENDIENTE").aggregate(s=Sum("monto"))["s"] or 0
    )

    ultima_multa = multas_qs.first()

    ctx = {
        "conductor": conductor,
        "docs": docs_qs,
        "vencidos": vencidos,
        "por_vencer": por_vencer,
        "vigentes": vigentes,
        "hoy": hoy,
        "limite": limite,
        "multas": multas_qs,
        "total_multas": total_multas,
        "monto_total": monto_total,
        "monto_pendiente": monto_pendiente,
        "ultima_multa": ultima_multa,
    }

    return render(request, "taller/reporte_conductor.html", ctx)


def reporte_conductor_pdf(request, conductor_id: int):
    """Genera PDF del reporte de conductor"""
    conductor = get_object_or_404(Conductor, pk=conductor_id)

    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)

    docs_qs = DocumentoConductor.objects.filter(conductor=conductor).order_by(
        "fecha_vencimiento"
    )

    docs_vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    docs_porvencer = docs_qs.filter(
        fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite
    ).count()
    docs_vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    # Generar PDF
    response = HttpResponse(content_type="application/pdf")
    filename = f"reporte_conductor_{conductor.rut or conductor.id}.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    x = 20 * mm
    y = height - 20 * mm

    # Encabezado
    p.setFont("Helvetica-Bold", 14)
    p.drawString(x, y, "Transcap ERP - Reporte de Conductor")
    y -= 10 * mm

    p.setFont("Helvetica", 10)
    p.drawString(x, y, f"Fecha emisión: {hoy.strftime('%d/%m/%Y')}")
    y -= 10 * mm

    # Datos del conductor
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Conductor")
    y -= 6 * mm

    p.setFont("Helvetica", 10)
    nombre_completo = f"{conductor.apellidos} {conductor.nombres}".strip()
    p.drawString(x, y, f"Nombre: {nombre_completo}")
    y -= 5 * mm
    if getattr(conductor, "rut", None):
        p.drawString(x, y, f"RUT: {conductor.rut}")
        y -= 5 * mm
    y -= 5 * mm

    # KPIs
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Resumen de documentos")
    y -= 6 * mm

    p.setFont("Helvetica", 10)
    p.drawString(
        x,
        y,
        f"Documentos vencidos / por vencer / vigentes: "
        f"{docs_vencidos} / {docs_porvencer} / {docs_vigentes}",
    )
    y -= 5 * mm
    p.drawString(
        x,
        y,
        f"Rango 'por vencer': hasta {limite.strftime('%d/%m/%Y')}",
    )
    y -= 10 * mm

    # Listado de documentos
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Detalle de documentos")
    y -= 6 * mm
    p.setFont("Helvetica", 9)

    for d in docs_qs:
        if y < 30 * mm:
            p.showPage()
            y = height - 20 * mm
            p.setFont("Helvetica-Bold", 12)
            p.drawString(x, y, "Detalle de documentos (cont.)")
            y -= 6 * mm
            p.setFont("Helvetica", 9)

        tipo_doc = getattr(d, "get_tipo_display", lambda: d.tipo)()
        emision = d.fecha_emision.strftime("%d/%m/%Y") if d.fecha_emision else "-"
        venc = d.fecha_vencimiento.strftime("%d/%m/%Y") if d.fecha_vencimiento else "-"

        if d.fecha_vencimiento and d.fecha_vencimiento < hoy:
            estado = "VENCIDO"
        elif d.fecha_vencimiento and d.fecha_vencimiento <= limite:
            estado = "POR VENCER"
        else:
            estado = "VIGENTE"

        linea = f"- {tipo_doc}: {emision} → {venc}  ({estado})"
        p.drawString(x, y, linea)
        y -= 4 * mm

        if d.descripcion:
            p.drawString(x + 5 * mm, y, d.descripcion[:90])
            y -= 4 * mm

    p.showPage()
    p.save()
    return response


def ranking_conductores_multas(request):
    """Ranking de conductores por cantidad de multas"""
    conductores = Conductor.objects.all().order_by("apellidos", "nombres")
    ranking = []

    for c in conductores:
        raw_multas = getattr(c, "multas", 0)

        if hasattr(raw_multas, "all"):
            total_multas = raw_multas.count()
        else:
            total_multas = raw_multas or 0

        if total_multas <= 0:
            continue

        c.total_multas = total_multas
        c.monto_total = Decimal("0")
        c.monto_pendiente = Decimal("0")
        c.ultima_multa = None

        ranking.append(c)

    ranking.sort(key=lambda x: x.total_multas, reverse=True)

    ctx = {
        "ranking": ranking,
    }
    return render(request, "taller/ranking_conductores_multas.html", ctx)


def reporte_conductor_selector(request):
    """Selector de conductor para reportes"""
    q = request.GET.get("q", "").strip()

    conductores = Conductor.objects.all().order_by("apellidos", "nombres")

    if q:
        conductores = conductores.filter(
            Q(apellidos__icontains=q)
            | Q(nombres__icontains=q)
            | Q(rut__icontains=q)
        )

    ctx = {
        "conductores": conductores,
        "q": q,
    }
    return render(request, "taller/reporte_conductor_selector.html", ctx)


# ============================================
# VISTAS PARA RUTAS DE VIAJE
# ============================================

@login_required
def rutas_viaje_lista(request):
    """Lista rutas de viaje con búsqueda"""
    q = request.GET.get("q", "").strip()

    rutas = RutaViaje.objects.all().order_by("origen", "destino", "nombre")

    if q:
        rutas = rutas.filter(
            Q(nombre__icontains=q)
            | Q(origen__icontains=q)
            | Q(destino__icontains=q)
        )

    paginator = Paginator(rutas, 20)
    page = request.GET.get("page")
    rutas_page = paginator.get_page(page)

    context = {
        "rutas": rutas_page,
        "q": q,
    }
    return render(request, "taller/rutas_viaje_lista.html", context)


@login_required
def rutas_viaje_crear(request):
    """Crea una nueva ruta de viaje"""
    if request.method == "POST":
        form = RutaViajeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ruta creada correctamente.")
            return redirect("taller_rutas_viaje_lista")
    else:
        form = RutaViajeForm()

    return render(
        request,
        "taller/rutas_viaje_form.html",
        {"form": form, "modo": "crear"},
    )


@login_required
def rutas_viaje_editar(request, pk):
    """Edita una ruta de viaje existente"""
    ruta = get_object_or_404(RutaViaje, pk=pk)

    if request.method == "POST":
        form = RutaViajeForm(request.POST, instance=ruta)
        if form.is_valid():
            form.save()
            messages.success(request, "Ruta actualizada correctamente.")
            return redirect("taller_rutas_viaje_lista")
    else:
        form = RutaViajeForm(instance=ruta)

    return render(
        request,
        "taller/rutas_viaje_form.html",
        {"form": form, "modo": "editar", "ruta": ruta},
    )


@login_required
def rutas_viaje_eliminar(request, pk):
    """Elimina una ruta de viaje"""
    ruta = get_object_or_404(RutaViaje, pk=pk)

    if request.method == "POST":
        ruta.delete()
        messages.success(request, "Ruta eliminada correctamente.")
        return redirect("taller_rutas_viaje_lista")

    return render(
        request,
        "taller/rutas_viaje_confirmar_eliminar.html",
        {"ruta": ruta},
    )


# ============================================
# VISTAS PARA COORDINACIÓN DE VIAJES
# ============================================

@login_required
def coordinacion_viajes_lista(request):
    q = request.GET.get("q", "").strip()

    # 👇 OJO: solo usamos campos que EXISTEN en el modelo
    viajes_qs = (
        CoordinacionViaje.objects
        .select_related("ruta", "conductor", "tracto_camion", "semirremolque")
        .order_by("-fecha_carga")
    )

    if q:
        viajes_qs = viajes_qs.filter(
            Q(origen__icontains=q)
            | Q(destino__icontains=q)
            | Q(ruta__nombre__icontains=q)
            | Q(conductor__nombres__icontains=q)
            | Q(conductor__apellidos__icontains=q)
            | Q(tracto_camion__patente__icontains=q)
            | Q(semirremolque__patente__icontains=q)
        )

    paginator = Paginator(viajes_qs, 20)
    page_number = request.GET.get("page")
    viajes_page = paginator.get_page(page_number)

    context = {
        "viajes": viajes_page,
        "q": q,
    }
    return render(request, "taller/coordinacion_viajes_lista.html", context)


@login_required
def coordinacion_viaje_crear(request):
    if request.method == "POST":
        form = CoordinacionViajeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Viaje creado correctamente.")
            return redirect("taller_coordinacion_viajes_lista")
    else:
        form = CoordinacionViajeForm()

    return render(request, "taller/coordinacion_viaje_form.html", {"form": form})


@login_required
def coordinacion_viaje_editar(request, pk):
    """Edita una coordinación de viaje existente"""
    viaje = get_object_or_404(CoordinacionViaje, pk=pk)

    if request.method == "POST":
        form = CoordinacionViajeForm(request.POST, instance=viaje)
        if form.is_valid():
            form.save()
            messages.success(request, "Viaje actualizado correctamente.")
            return redirect("taller_coordinacion_viajes_lista")
    else:
        form = CoordinacionViajeForm(instance=viaje)

    return render(
        request,
        "taller/coordinacion_viaje_form.html",
        {"form": form, "modo": "editar", "viaje": viaje},
    )


@login_required
def coordinacion_viaje_eliminar(request, pk):
    """Elimina una coordinación de viaje"""
    viaje = get_object_or_404(CoordinacionViaje, pk=pk)

    if request.method == "POST":
        viaje.delete()
        messages.success(request, "Viaje eliminado correctamente.")
        return redirect("taller_coordinacion_viajes_lista")

    return render(
        request,
        "taller/coordinacion_viaje_confirmar_eliminar.html",
        {"viaje": viaje},
    )
    
# En views.py, agrega esta vista temporal para debug
def debug_vehiculos_tipo(request):
    """Vista temporal para debug - ver vehículos por tipo"""
   
    
    tractos = Vehiculo.objects.filter(tipo="TRACTO", activo=True)
    semirremolques = Vehiculo.objects.filter(tipo="SEMIRREMOLQUE", activo=True)
    todos = Vehiculo.objects.all()
    
    context = {
        'tractos': tractos,
        'semirremolques': semirremolques,
        'todos': todos,
        'tipos_count': Vehiculo.objects.values('tipo').annotate(total=Count('id')),
    }
    
    return render(request, "taller/debug_vehiculos.html", context)




def get_ruta_detalle(request, ruta_id):
    """API para obtener detalles de una ruta (origen/destino)"""
    try:
        ruta = RutaViaje.objects.get(id=ruta_id)
        return JsonResponse({
            'success': True,
            'origen': ruta.origen,
            'destino': ruta.destino,
            'distancia': str(ruta.distancia_km) if ruta.distancia_km else None,
        })
    except RutaViaje.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ruta no encontrada'})
    
    
# En views.py, agregar la siguiente vista:



def coordinacion_viaje_pdf(request, pk):
    """Genera PDF de la coordinación de viaje"""
    viaje = get_object_or_404(CoordinacionViaje, pk=pk)

    # Crear la respuesta HTTP con el PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"coordinacion_viaje_{viaje.id}_{viaje.fecha_carga}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    # Crear el PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Configuración
    x = 20 * mm
    y = height - 20 * mm

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(x, y, "TRANSCAP - Coordinación de Viaje")
    y -= 10 * mm

    # Fecha de emisión
    p.setFont("Helvetica", 10)
    from django.utils import timezone
    hoy = timezone.now().date()
    p.drawString(x, y, f"Fecha de emisión: {hoy.strftime('%d/%m/%Y')}")
    y -= 15 * mm

    # Datos del viaje
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Datos del Viaje")
    y -= 8 * mm

    p.setFont("Helvetica", 10)
    # Fechas
    p.drawString(x, y, f"Fecha de carga: {viaje.fecha_carga.strftime('%d/%m/%Y')}")
    y -= 5 * mm
    if viaje.fecha_descarga:
        p.drawString(x, y, f"Fecha de descarga: {viaje.fecha_descarga.strftime('%d/%m/%Y')}")
        y -= 5 * mm
    # Sobrestadía
    if viaje.sobreestadia_dias:
        p.drawString(x, y, f"Sobreestadía: {viaje.sobreestadia_dias} días")
        y -= 5 * mm
    # Estado
    p.drawString(x, y, f"Estado: {viaje.get_estado_display()}")
    y -= 5 * mm
    # Ruta
    if viaje.ruta:
        p.drawString(x, y, f"Ruta: {viaje.ruta.nombre}")
        y -= 5 * mm
    # Origen y Destino
    p.drawString(x, y, f"Origen: {viaje.origen}")
    y -= 5 * mm
    p.drawString(x, y, f"Destino: {viaje.destino}")
    y -= 10 * mm

    # Conductor
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Conductor")
    y -= 8 * mm
    p.setFont("Helvetica", 10)
    if viaje.conductor:
        p.drawString(x, y, f"Nombre: {viaje.conductor.nombre_completo}")
        y -= 5 * mm
        p.drawString(x, y, f"RUT: {viaje.conductor.rut}")
        y -= 5 * mm
        if viaje.conductor.licencia_clase:
            p.drawString(x, y, f"Licencia: {viaje.conductor.licencia_clase}")
            y -= 5 * mm
        if viaje.conductor.licencia_vencimiento:
            p.drawString(x, y, f"Vencimiento licencia: {viaje.conductor.licencia_vencimiento.strftime('%d/%m/%Y')}")
            y -= 5 * mm
    else:
        p.drawString(x, y, "No asignado")
        y -= 5 * mm
    y -= 10 * mm

    # Vehículos
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Vehículos")
    y -= 8 * mm
    p.setFont("Helvetica", 10)
    # Tracto camión
    if viaje.tracto_camion:
        p.drawString(x, y, f"Tracto camión: {viaje.tracto_camion.patente} - {viaje.tracto_camion.marca} {viaje.tracto_camion.modelo}")
        y -= 5 * mm
    else:
        p.drawString(x, y, "Tracto camión: No asignado")
        y -= 5 * mm
    # Semirremolque
    if viaje.semirremolque:
        p.drawString(x, y, f"Semirremolque: {viaje.semirremolque.patente} - {viaje.semirremolque.marca} {viaje.semirremolque.modelo}")
        y -= 5 * mm
    else:
        p.drawString(x, y, "Semirremolque: No asignado")
        y -= 5 * mm
    y -= 10 * mm

    # Observaciones
    if viaje.observaciones:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(x, y, "Observaciones")
        y -= 8 * mm
        p.setFont("Helvetica", 10)
        # Dividir el texto en líneas
        observaciones = viaje.observaciones
        # Simple manejo de texto largo (esto es básico, se puede mejorar)
        lines = []
        words = observaciones.split()
        line = ""
        for word in words:
            if len(line) + len(word) < 80:
                line += word + " "
            else:
                lines.append(line)
                line = word + " "
        if line:
            lines.append(line)
        for line in lines:
            if y < 50 * mm:  # Si se acerca al final de la página, crear una nueva
                p.showPage()
                y = height - 20 * mm
                p.setFont("Helvetica", 10)
            p.drawString(x, y, line)
            y -= 5 * mm

    p.showPage()
    p.save()

    return response