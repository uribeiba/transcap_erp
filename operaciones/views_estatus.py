from __future__ import annotations

from io import BytesIO
from typing import Dict, List, Optional, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from taller.models import Conductor

from .models import EstatusOperacionalViaje, TurnoEstatus


def _parse_fecha(value: Optional[str]):
    """
    Reutilizable y tolerante.
    Acepta YYYY-MM-DD (input type=date).
    """
    if not value:
        return timezone.localdate()
    try:
        # "2026-03-02"
        return timezone.datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return timezone.localdate()


def _get_conductores_queryset():
    """
    Si tienes campo 'activo' en Conductor, úsalo.
    Si no existe, devuelve todos (seguro).
    """
    try:
        # Si existe 'activo' (boolean) en tu modelo
        Conductor._meta.get_field("activo")
        return Conductor.objects.filter(activo=True)
    except Exception:
        return Conductor.objects.all()


def _build_planilla_rows(fecha) -> Tuple[List[Dict], List[Conductor], List[Conductor]]:
    """
    Devuelve:
      - rows: lista por chofer con AM/PM (texto, tracto, rampla)
      - missing_am: lista choferes sin AM
      - missing_pm: lista choferes sin PM
    """
    conductores = list(_get_conductores_queryset().order_by("apellidos", "nombres"))

    am = (
        EstatusOperacionalViaje.objects.select_related("tracto", "rampla", "conductor")
        .filter(fecha=fecha, turno=TurnoEstatus.AM)
    )
    pm = (
        EstatusOperacionalViaje.objects.select_related("tracto", "rampla", "conductor")
        .filter(fecha=fecha, turno=TurnoEstatus.PM)
    )

    am_map = {r.conductor_id: r for r in am}
    pm_map = {r.conductor_id: r for r in pm}

    missing_am = [c for c in conductores if c.id not in am_map]
    missing_pm = [c for c in conductores if c.id not in pm_map]

    rows: List[Dict] = []
    for c in conductores:
        r_am = am_map.get(c.id)
        r_pm = pm_map.get(c.id)

        # Preferir patentes del registro (AM/PM); si PM está vacío, usa AM como fallback.
        tracto = getattr(r_pm, "tracto", None) or getattr(r_am, "tracto", None)
        rampla = getattr(r_pm, "rampla", None) or getattr(r_am, "rampla", None)

        rows.append(
            {
                "conductor": c,
                "tracto": tracto,
                "rampla": rampla,
                "am_texto": (getattr(r_am, "estado_texto", "") or "").strip(),
                "pm_texto": (getattr(r_pm, "estado_texto", "") or "").strip(),
                "has_am": r_am is not None,
                "has_pm": r_pm is not None,
            }
        )

    return rows, missing_am, missing_pm


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_planilla(request: HttpRequest):
    """
    Vista PRO+: planilla por fecha con columnas AM/PM.
    """
    fecha = _parse_fecha(request.GET.get("fecha"))
    q = (request.GET.get("q") or "").strip()

    rows, missing_am, missing_pm = _build_planilla_rows(fecha)

    # Filtro de búsqueda (pro+)
    if q:
        q_low = q.lower()
        filtered = []
        for r in rows:
            c: Conductor = r["conductor"]
            if (
                q_low in (c.nombres or "").lower()
                or q_low in (c.apellidos or "").lower()
                or q_low in (c.rut or "").lower()
                or q_low in (getattr(r["tracto"], "patente", "") or "").lower()
                or q_low in (getattr(r["rampla"], "patente", "") or "").lower()
                or q_low in (r["am_texto"] or "").lower()
                or q_low in (r["pm_texto"] or "").lower()
            ):
                filtered.append(r)
        rows = filtered

        # missing lists no se filtran por q (para que veas faltantes reales del día)
        # Si quieres que también se filtren, lo hacemos.

    return render(
        request,
        "operaciones/estatus_viajes_planilla.html",
        {
            "fecha": fecha,
            "q": q,
            "rows": rows,
            "missing_am": missing_am,
            "missing_pm": missing_pm,
        },
    )


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_export_planilla_xlsx(request: HttpRequest):
    """
    Export XLSX en formato planilla (AM/PM en columnas).
    """
    fecha = _parse_fecha(request.GET.get("fecha"))
    q = (request.GET.get("q") or "").strip()

    rows, missing_am, missing_pm = _build_planilla_rows(fecha)

    if q:
        q_low = q.lower()
        rows = [
            r
            for r in rows
            if (
                q_low in (r["conductor"].nombres or "").lower()
                or q_low in (r["conductor"].apellidos or "").lower()
                or q_low in (r["conductor"].rut or "").lower()
                or q_low in (getattr(r["tracto"], "patente", "") or "").lower()
                or q_low in (getattr(r["rampla"], "patente", "") or "").lower()
                or q_low in (r["am_texto"] or "").lower()
                or q_low in (r["pm_texto"] or "").lower()
            )
        ]

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font
    except Exception:
        messages.error(request, "Falta openpyxl. Instala con: pip install openpyxl")
        return redirect("operaciones:estatus_viajes_planilla")

    wb = Workbook()
    ws = wb.active
    ws.title = "Estatus Planilla"

    # Header
    ws.append(
        [
            "Chofer",
            "RUT",
            "Tracto",
            "Rampla",
            "AM",
            "PM",
        ]
    )
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Rows
    for r in rows:
        c = r["conductor"]
        ws.append(
            [
                f"{c.nombres} {c.apellidos}".strip(),
                c.rut,
                getattr(r["tracto"], "patente", "") or "",
                getattr(r["rampla"], "patente", "") or "",
                r["am_texto"],
                r["pm_texto"],
            ]
        )

    # Ajustes visuales mínimos
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 60
    ws.column_dimensions["F"].width = 60

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=6):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    filename = f"estatus_planilla_{fecha.strftime('%Y%m%d')}.xlsx"
    resp = HttpResponse(
        bio.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp