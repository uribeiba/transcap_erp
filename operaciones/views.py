from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import EstatusOperacionalViajeForm
from .models import EstatusOperacionalViaje, TurnoEstatus
from taller.models import Conductor

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _parse_fecha(fecha_str: str):
    fecha_str = (fecha_str or "").strip()
    if fecha_str:
        try:
            return timezone.datetime.fromisoformat(fecha_str).date()
        except Exception:
            return timezone.localdate()
    return timezone.localdate()


def _turnos_a_mostrar(turno_param: str):
    turno_param = (turno_param or "TODOS").upper()
    if turno_param in [TurnoEstatus.AM, TurnoEstatus.PM]:
        return [turno_param]
    return [TurnoEstatus.AM, TurnoEstatus.PM]


# ============================================================
# Estatus de Viajes (AM/PM)
# ============================================================

@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
def estatus_viajes_panel(request):
    fecha = _parse_fecha(request.GET.get("fecha"))
    turno = (request.GET.get("turno") or "TODOS").upper()
    q = (request.GET.get("q") or "").strip()
    turnos = _turnos_a_mostrar(turno)

    qs = (EstatusOperacionalViaje.objects
          .select_related("conductor", "tracto", "rampla")
          .filter(fecha=fecha, turno__in=turnos)
          .order_by("conductor__apellidos", "conductor__nombres", "turno"))

    if q:
        qs = qs.filter(
            Q(conductor__nombres__icontains=q) |
            Q(conductor__apellidos__icontains=q) |
            Q(conductor__rut__icontains=q) |
            Q(tracto__patente__icontains=q) |
            Q(rampla__patente__icontains=q) |
            Q(estado_texto__icontains=q)
        )

    # Choferes faltantes
    conductores_activos = Conductor.objects.filter(activo=True).order_by("apellidos", "nombres")
    existentes_am = set(EstatusOperacionalViaje.objects.filter(fecha=fecha, turno=TurnoEstatus.AM).values_list("conductor_id", flat=True))
    existentes_pm = set(EstatusOperacionalViaje.objects.filter(fecha=fecha, turno=TurnoEstatus.PM).values_list("conductor_id", flat=True))
    missing_am = [c for c in conductores_activos if c.id not in existentes_am]
    missing_pm = [c for c in conductores_activos if c.id not in existentes_pm]

    form = EstatusOperacionalViajeForm(initial={"fecha": fecha, "turno": turnos[0]})

    return render(request, "operaciones/estatus_viajes.html", {
        "fecha": fecha,
        "turno": turno,
        "q": q,
        "items": qs,
        "form": form,
        "turnos": ["TODOS", TurnoEstatus.AM, TurnoEstatus.PM],
        "missing_am": missing_am,
        "missing_pm": missing_pm,
    })


@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_POST
def estatus_viajes_guardar(request):
    form = EstatusOperacionalViajeForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Revisa el formulario: hay campos inválidos.")
        return redirect("operaciones:estatus_viajes_panel")

    d = form.cleaned_data
    obj, created = EstatusOperacionalViaje.objects.get_or_create(
        fecha=d["fecha"], turno=d["turno"], conductor=d["conductor"],
        defaults={
            "tracto": d.get("tracto"),
            "rampla": d.get("rampla"),
            "estado_texto": (d.get("estado_texto") or "").strip(),
            "creado_por": request.user,
            "actualizado_por": request.user,
        }
    )
    if not created:
        obj.tracto = d.get("tracto")
        obj.rampla = d.get("rampla")
        obj.estado_texto = (d.get("estado_texto") or "").strip()
        obj.actualizado_por = request.user
        obj.save()

    messages.success(request, "Estatus guardado ✅")
    return redirect("operaciones:estatus_viajes_panel")


@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_POST
def estatus_viajes_eliminar(request, pk):
    obj = get_object_or_404(EstatusOperacionalViaje, pk=pk)
    obj.delete()
    messages.success(request, "Estatus eliminado.")
    return redirect("operaciones:estatus_viajes_panel")


@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_POST
def estatus_viajes_copiar_am_a_pm(request):
    fecha = _parse_fecha(request.POST.get("fecha"))

    am_rows = list(EstatusOperacionalViaje.objects.filter(fecha=fecha, turno=TurnoEstatus.AM))
    creados = 0
    actualizados = 0

    for r in am_rows:
        obj, created = EstatusOperacionalViaje.objects.get_or_create(
            fecha=fecha, turno=TurnoEstatus.PM, conductor=r.conductor,
            defaults={
                "tracto": r.tracto,
                "rampla": r.rampla,
                "estado_texto": (r.estado_texto or "").strip(),
                "creado_por": request.user,
                "actualizado_por": request.user,
            }
        )
        if created:
            creados += 1
        else:
            changed = False
            if not (obj.estado_texto or "").strip() and (r.estado_texto or "").strip():
                obj.estado_texto = (r.estado_texto or "").strip()
                changed = True
            if obj.tracto_id is None and r.tracto_id is not None:
                obj.tracto = r.tracto
                changed = True
            if obj.rampla_id is None and r.rampla_id is not None:
                obj.rampla = r.rampla
                changed = True
            if changed:
                obj.actualizado_por = request.user
                obj.save()
                actualizados += 1

    messages.success(request, f"Copiado AM → PM. Nuevos: {creados} | Actualizados: {actualizados}")
    return redirect("operaciones:estatus_viajes_panel")


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_export_xlsx(request):
    fecha = _parse_fecha(request.GET.get("fecha"))
    turno = (request.GET.get("turno") or "TODOS").upper()
    q = (request.GET.get("q") or "").strip()
    turnos = _turnos_a_mostrar(turno)

    qs = (EstatusOperacionalViaje.objects.select_related("conductor", "tracto", "rampla")
          .filter(fecha=fecha, turno__in=turnos)
          .order_by("conductor__apellidos", "conductor__nombres", "turno"))

    if q:
        qs = qs.filter(
            Q(conductor__nombres__icontains=q) |
            Q(conductor__apellidos__icontains=q) |
            Q(conductor__rut__icontains=q) |
            Q(tracto__patente__icontains=q) |
            Q(rampla__patente__icontains=q) |
            Q(estado_texto__icontains=q)
        )

    try:
        from openpyxl import Workbook
    except ImportError:
        messages.error(request, "Falta openpyxl. Instala con: pip install openpyxl")
        return redirect("operaciones:estatus_viajes_panel")

    wb = Workbook()
    ws = wb.active
    ws.title = "Estatus"
    ws.append(["Fecha", "Turno", "Chofer", "RUT", "Tracto", "Rampla", "Estado", "Actualizado"])

    for r in qs:
        ws.append([
            r.fecha.strftime("%d-%m-%Y"),
            r.turno,
            f"{r.conductor.nombres} {r.conductor.apellidos}",
            r.conductor.rut,
            getattr(r.tracto, "patente", "") or "",
            getattr(r.rampla, "patente", "") or "",
            (r.estado_texto or "").strip(),
            timezone.localtime(r.actualizado_el).strftime("%d-%m-%Y %H:%M"),
        ])

    from io import BytesIO
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    filename = f"estatus_viajes_{fecha.strftime('%Y%m%d')}_{turno if turno!='TODOS' else 'ALL'}.xlsx"
    resp = HttpResponse(
        bio.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp