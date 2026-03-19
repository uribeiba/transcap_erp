from __future__ import annotations
from io import BytesIO
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import models, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from taller.models import Conductor
from .forms import EstatusOperacionalViajeForm
from .models import EstatusOperacionalViaje, TurnoEstatus

from operaciones.models import EstatusOperacionalViaje
from bitacora.models import Bitacora





from operaciones.models import EstatusOperacionalViaje



def _parse_fecha(value: str | None):
    if not value:
        return timezone.localdate()
    try:
        return timezone.datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return timezone.localdate()


def _turnos_a_mostrar(turno_param: str):
    turno_param = (turno_param or "TODOS").upper()
    if turno_param in [TurnoEstatus.AM, TurnoEstatus.PM]:
        return [turno_param]
    return [TurnoEstatus.AM, TurnoEstatus.PM]


def _get_conductores_queryset():
    try:
        Conductor._meta.get_field("activo")
        return Conductor.objects.filter(activo=True)
    except Exception:
        return Conductor.objects.all()


def _qs_estatus(fecha, turnos, q=""):
    qs = (
        EstatusOperacionalViaje.objects
        .select_related("conductor", "tracto", "rampla", "cliente")
        .filter(fecha=fecha, turno__in=turnos)
        .order_by("conductor__apellidos", "conductor__nombres", "turno")
    )

    q = (q or "").strip()
    if q:
        qs = qs.filter(
            models.Q(conductor__nombres__icontains=q)
            | models.Q(conductor__apellidos__icontains=q)
            | models.Q(conductor__rut__icontains=q)
            | models.Q(tracto__patente__icontains=q)
            | models.Q(rampla__patente__icontains=q)
            | models.Q(cliente__razon_social__icontains=q)
            | models.Q(cliente__rut__icontains=q)
            | models.Q(nro_guia__icontains=q)
            | models.Q(estado_guia__icontains=q)
            | models.Q(estado_carga__icontains=q)
            | models.Q(lugar_carga__icontains=q)
            | models.Q(lugar_descarga__icontains=q)
            | models.Q(estado_texto__icontains=q)
            | models.Q(observaciones__icontains=q)
        )
    return qs


def _missing_por_turno(fecha):
    conductores = _get_conductores_queryset().order_by("apellidos", "nombres")
    existentes_am = set(
        EstatusOperacionalViaje.objects.filter(fecha=fecha, turno=TurnoEstatus.AM)
        .values_list("conductor_id", flat=True)
    )
    existentes_pm = set(
        EstatusOperacionalViaje.objects.filter(fecha=fecha, turno=TurnoEstatus.PM)
        .values_list("conductor_id", flat=True)
    )

    missing_am = [c for c in conductores if c.id not in existentes_am]
    missing_pm = [c for c in conductores if c.id not in existentes_pm]
    return missing_am, missing_pm


def _estado_badge_count(qs, estado_carga):
    return qs.filter(estado_carga=estado_carga).count()


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
def estatus_viajes_panel(request: HttpRequest):
    fecha = _parse_fecha(request.GET.get("fecha"))
    turno = (request.GET.get("turno") or "TODOS").upper()
    q = (request.GET.get("q") or "").strip()
    turnos = _turnos_a_mostrar(turno)

    qs = _qs_estatus(fecha, turnos, q)

    missing_am, missing_pm = _missing_por_turno(fecha)

    form = EstatusOperacionalViajeForm(
        initial={
            "fecha": fecha,
            "turno": TurnoEstatus.AM if turno == "TODOS" else turno,
        }
    )

    context = {
        "fecha": fecha,
        "turno": turno,
        "q": q,
        "items": qs,
        "form": form,
        "turnos": ["TODOS", TurnoEstatus.AM, TurnoEstatus.PM],
        "missing_am": missing_am,
        "missing_pm": missing_pm,
        "total_registros": qs.count(),
        "total_descargado": _estado_badge_count(qs, EstatusOperacionalViaje.EstadoCargaChoices.DESCARGADO),
        "total_camino_descargar": _estado_badge_count(qs, EstatusOperacionalViaje.EstadoCargaChoices.CAMINO_DESCARGAR),
        "total_retorno_vacio": _estado_badge_count(qs, EstatusOperacionalViaje.EstadoCargaChoices.RETORNO_VACIO),
    }
    return render(request, "operaciones/estatus_viajes.html", context)


def _estatus_redirect(request):
    fecha = request.POST.get("fecha") or request.GET.get("fecha") or ""
    turno = request.POST.get("turno") or request.GET.get("turno") or "TODOS"
    q = request.POST.get("q") or request.GET.get("q") or ""

    params = {}
    if fecha:
        params["fecha"] = fecha
    if turno:
        params["turno"] = turno
    if q:
        params["q"] = q

    url = reverse("operaciones:estatus_viajes_panel")
    return f"{url}?{urlencode(params)}" if params else url


@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_POST
def estatus_viajes_guardar(request: HttpRequest):
    form = EstatusOperacionalViajeForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Revisa el formulario: hay campos inválidos.")
        return redirect(_estatus_redirect(request))

    d = form.cleaned_data

    with transaction.atomic():
        obj, created = EstatusOperacionalViaje.objects.select_for_update().get_or_create(
            fecha=d["fecha"],
            turno=d["turno"],
            conductor=d["conductor"],
            defaults={
                "tracto": d.get("tracto"),
                "rampla": d.get("rampla"),
                "cliente": d.get("cliente"),
                "nro_guia": d.get("nro_guia"),
                "estado_guia": d.get("estado_guia"),
                "estado_carga": d.get("estado_carga"),
                "lugar_carga": d.get("lugar_carga"),
                "fecha_carga": d.get("fecha_carga"),
                "lugar_descarga": d.get("lugar_descarga"),
                "fecha_descarga": d.get("fecha_descarga"),
                "estado_texto": d.get("estado_texto"),
                "observaciones": d.get("observaciones"),
                "creado_por": request.user,
                "actualizado_por": request.user,
            },
        )

        if not created:
            obj.tracto = d.get("tracto")
            obj.rampla = d.get("rampla")
            obj.cliente = d.get("cliente")
            obj.nro_guia = d.get("nro_guia")
            obj.estado_guia = d.get("estado_guia")
            obj.estado_carga = d.get("estado_carga")
            obj.lugar_carga = d.get("lugar_carga")
            obj.fecha_carga = d.get("fecha_carga")
            obj.lugar_descarga = d.get("lugar_descarga")
            obj.fecha_descarga = d.get("fecha_descarga")
            obj.estado_texto = d.get("estado_texto")
            obj.observaciones = d.get("observaciones")
            obj.actualizado_por = request.user
            obj.save()

    messages.success(request, "Estatus guardado correctamente.")
    return redirect(_estatus_redirect(request))


@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_POST
def estatus_viajes_eliminar(request: HttpRequest, pk: int):
    obj = get_object_or_404(EstatusOperacionalViaje, pk=pk)
    obj.delete()
    messages.success(request, "Estatus eliminado.")
    return redirect(_estatus_redirect(request))


@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_POST
def estatus_viajes_copiar_am_a_pm(request: HttpRequest):
    fecha = _parse_fecha(request.POST.get("fecha"))

    am_rows = list(EstatusOperacionalViaje.objects.filter(fecha=fecha, turno=TurnoEstatus.AM))
    creados = 0
    actualizados = 0

    for r in am_rows:
        obj, created = EstatusOperacionalViaje.objects.get_or_create(
            fecha=fecha,
            turno=TurnoEstatus.PM,
            conductor=r.conductor,
            defaults={
                "tracto": r.tracto,
                "rampla": r.rampla,
                "cliente": r.cliente,
                "nro_guia": r.nro_guia,
                "estado_guia": r.estado_guia,
                "estado_carga": r.estado_carga,
                "lugar_carga": r.lugar_carga,
                "fecha_carga": r.fecha_carga,
                "lugar_descarga": r.lugar_descarga,
                "fecha_descarga": r.fecha_descarga,
                "estado_texto": r.estado_texto,
                "observaciones": r.observaciones,
                "creado_por": request.user,
                "actualizado_por": request.user,
            },
        )
        if created:
            creados += 1
        else:
            obj.tracto = obj.tracto or r.tracto
            obj.rampla = obj.rampla or r.rampla
            obj.cliente = obj.cliente or r.cliente
            obj.nro_guia = obj.nro_guia or r.nro_guia
            obj.estado_guia = obj.estado_guia or r.estado_guia
            obj.estado_carga = obj.estado_carga or r.estado_carga
            obj.lugar_carga = obj.lugar_carga or r.lugar_carga
            obj.fecha_carga = obj.fecha_carga or r.fecha_carga
            obj.lugar_descarga = obj.lugar_descarga or r.lugar_descarga
            obj.fecha_descarga = obj.fecha_descarga or r.fecha_descarga
            obj.estado_texto = obj.estado_texto or r.estado_texto
            obj.observaciones = obj.observaciones or r.observaciones
            obj.actualizado_por = request.user
            obj.save()
            actualizados += 1

    messages.success(request, f"Copiado AM → PM. Nuevos: {creados} | Actualizados: {actualizados}")
    return redirect(reverse("operaciones:estatus_viajes_panel") + f"?fecha={fecha.isoformat()}")


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_export_xlsx(request: HttpRequest):
    fecha = _parse_fecha(request.GET.get("fecha"))
    turno = (request.GET.get("turno") or "TODOS").upper()
    q = (request.GET.get("q") or "").strip()
    turnos = _turnos_a_mostrar(turno)

    qs = _qs_estatus(fecha, turnos, q)

    wb = Workbook()
    ws = wb.active
    ws.title = "Estatus Viajes"

    headers = [
        "Turno",
        "Chofer",
        "RUT",
        "Pte Tracto",
        "Pte Semirremolque",
        "Estado Carga",
        "Nro Guía",
        "Estado Guía",
        "Cliente",
        "Lugar Carga",
        "Fecha Carga",
        "Lugar Descarga",
        "Fecha Descarga",
        "Observaciones",
    ]
    ws.append(headers)

    header_fill = PatternFill("solid", fgColor="1F1F1F")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    fill_ok = PatternFill("solid", fgColor="9ACD32")
    fill_warn = PatternFill("solid", fgColor="FFD966")
    fill_info = PatternFill("solid", fgColor="FFF200")

    for r in qs:
        row = [
            r.turno,
            f"{r.conductor.nombres} {r.conductor.apellidos}".strip(),
            r.conductor.rut,
            getattr(r.tracto, "patente", "") or "",
            getattr(r.rampla, "patente", "") or "",
            r.get_estado_carga_display(),
            r.nro_guia,
            r.estado_guia,
            getattr(r.cliente, "razon_social", "") or "",
            r.lugar_carga,
            r.fecha_carga.strftime("%d.%m.%Y") if r.fecha_carga else "",
            r.lugar_descarga,
            r.fecha_descarga.strftime("%d.%m.%Y") if r.fecha_descarga else "",
            r.observaciones,
        ]
        ws.append(row)

        excel_row = ws.max_row
        if r.estado_carga == EstatusOperacionalViaje.EstadoCargaChoices.DESCARGADO:
            fill = fill_ok
        elif r.estado_carga == EstatusOperacionalViaje.EstadoCargaChoices.CAMINO_DESCARGAR:
            fill = fill_info
        else:
            fill = fill_warn

        for cell in ws[excel_row]:
            cell.fill = fill

    widths = {
        "A": 8, "B": 28, "C": 16, "D": 14, "E": 18, "F": 20, "G": 14,
        "H": 16, "I": 24, "J": 22, "K": 14, "L": 22, "M": 14, "N": 30,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    filename = f"estatus_viajes_{fecha.strftime('%Y%m%d')}.xlsx"
    resp = HttpResponse(
        bio.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp



@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_a_bitacora(request: HttpRequest, pk: int):
    obj = get_object_or_404(
        EstatusOperacionalViaje.objects.select_related("cliente", "conductor", "tracto", "rampla"),
        pk=pk,
    )

    descripcion = obj.estado_texto or ""
    if obj.observaciones:
        descripcion = f"{descripcion}\n{obj.observaciones}".strip()

    # Buscar si ya existe una bitácora generada desde este estatus
    bitacora = (
        Bitacora.objects.filter(estatus_origen=obj)
        .order_by("-id")
        .first()
    )

    if bitacora:
        # SINCRONIZAR SIEMPRE los datos principales desde estatus
        bitacora.cliente = obj.cliente
        bitacora.conductor = obj.conductor
        bitacora.tracto = obj.tracto
        bitacora.rampla = obj.rampla

        bitacora.origen = obj.lugar_carga or ""
        bitacora.destino = obj.lugar_descarga or ""

        # Mapeo de fechas
        bitacora.fecha = obj.fecha
        bitacora.fecha_arribo = obj.fecha_carga
        bitacora.fecha_descarga = obj.fecha_descarga

        bitacora.guias_raw = obj.nro_guia or ""
        bitacora.descripcion_trabajo = descripcion

        if not bitacora.coordinador:
            bitacora.coordinador = (
                getattr(request.user, "get_full_name", lambda: "")() or request.user.username
            )

        bitacora.save()

        messages.info(
            request,
            "La bitácora ya existía y fue actualizada con los datos del estatus antes de abrirla."
        )
        return redirect("bitacora:editar", bitacora.id)

    # Si no existe, crear nueva
    bitacora = Bitacora.objects.create(
        estatus_origen=obj,
        cliente=obj.cliente,
        conductor=obj.conductor,
        tracto=obj.tracto,
        rampla=obj.rampla,
        origen=obj.lugar_carga or "",
        destino=obj.lugar_descarga or "",
        fecha=obj.fecha,
        fecha_arribo=obj.fecha_carga,
        fecha_descarga=obj.fecha_descarga,
        guias_raw=obj.nro_guia or "",
        descripcion_trabajo=descripcion,
        coordinador=getattr(request.user, "get_full_name", lambda: "")() or request.user.username,
        creado_por=request.user,
    )

    messages.success(request, "Bitácora creada desde Estatus de Viajes.")
    return redirect("bitacora:editar", bitacora.id)


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_planilla(request: HttpRequest):
    fecha = _parse_fecha(request.GET.get("fecha"))
    turno = (request.GET.get("turno") or "TODOS").upper()
    q = (request.GET.get("q") or "").strip()
    turnos = _turnos_a_mostrar(turno)

    rows = _qs_estatus(fecha, turnos, q)

    return render(
        request,
        "operaciones/estatus_viajes_planilla.html",
        {
            "fecha": fecha,
            "turno": turno,
            "q": q,
            "rows": rows,
        },
    )


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_export_planilla_xlsx(request: HttpRequest):
    return estatus_viajes_export_xlsx(request)