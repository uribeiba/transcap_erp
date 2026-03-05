from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import EstadoFacturacionGuiaForm
from .models import EstadoFacturacionGuia, EstadoRegistro

from django.db import models  # <- si no lo tienes
from .forms import EstadoFacturacionGuiaForm, EstatusOperacionalViajeForm
from .models import EstadoFacturacionGuia, EstadoRegistro, EstatusOperacionalViaje, TurnoEstatus

from django.http import HttpResponse
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


def _base_qs_por_fecha_y_q(fecha, q: str):
    qs = EstadoFacturacionGuia.objects.select_related(
        "cliente", "origen", "destino", "bloqueado_por"
    ).filter(fecha=fecha)

    q = (q or "").strip()
    if q:
        # OJO: usamos OR con union de QuerySets (como tú lo tenías)
        qs = (
            qs.filter(cliente__nombre__icontains=q)
            | qs.filter(nro_guia__icontains=q)
            | qs.filter(nro_factura__icontains=q)
            | qs.filter(referencia_viaje__icontains=q)
        )
    return qs


def _user_label(u):
    if not u:
        return ""
    full = (getattr(u, "get_full_name", lambda: "")() or "").strip()
    return full or getattr(u, "username", "") or str(u)


# ------------------------------------------------------------
# Tablero principal
# ------------------------------------------------------------

@login_required
@permission_required("operaciones.puede_ver_estado", raise_exception=True)
def tablero_diario(request):
    fecha = _parse_fecha(request.GET.get("fecha", ""))
    tab = (request.GET.get("tab") or EstadoRegistro.PENDIENTE).strip()
    q = (request.GET.get("q") or "").strip()

    base_qs = _base_qs_por_fecha_y_q(fecha, q)

    # -----------------------------
    # Conteos por estado (YA EXISTENTE)
    # -----------------------------
    conteos = dict(
        base_qs.values("estado").annotate(c=Count("id")).values_list("estado", "c")
    )
    total_monto = base_qs.aggregate(total=Sum("monto"))["total"] or 0
    registros = base_qs.filter(estado=tab).order_by("prioridad", "-id")[:400]

    # -----------------------------
    # PANEL PRO++ (ya lo habíamos agregado)
    # -----------------------------
    total_registros = base_qs.count()
    pendientes = conteos.get(getattr(EstadoRegistro, "PENDIENTE", "PEND"), 0)
    en_proceso = conteos.get(getattr(EstadoRegistro, "EN_PROCESO", "PROC"), 0)
    completados = conteos.get(getattr(EstadoRegistro, "COMPLETADO", "DONE"), 0)
    cancelados = conteos.get(getattr(EstadoRegistro, "CANCELADO", "CANC"), 0)

    # -----------------------------
    # ✅ ALERTAS PRO+++ (nuevas)
    # -----------------------------
    # Nota: usamos tu base_qs (respeta fecha + búsqueda q)
    # Si quieres que las alertas IGNOREN q, lo cambiamos a _base_qs_por_fecha_y_q(fecha, "")
    qs_alerta = _base_qs_por_fecha_y_q(fecha, "")

    sin_guia = qs_alerta.filter(models.Q(nro_guia__isnull=True) | models.Q(nro_guia="")).count()
    sin_factura = qs_alerta.filter(models.Q(nro_factura__isnull=True) | models.Q(nro_factura="")).count()
    sin_viaje = qs_alerta.filter(models.Q(referencia_viaje__isnull=True) | models.Q(referencia_viaje="")).count()
    sin_monto = qs_alerta.filter(models.Q(monto__isnull=True) | models.Q(monto=0)).count()
    urgentes_pend = qs_alerta.filter(prioridad="URG", estado=getattr(EstadoRegistro, "PENDIENTE", "PEND")).count()

    # Cada alerta tiene:
    # - label: texto
    # - count: número
    # - level: color (info/warning/danger)
    # - href: link directo a tablero con filtro
    alertas = []
    if sin_guia:
        alertas.append({
            "label": "Registros sin guía",
            "count": sin_guia,
            "level": "warning",
            "href": f"?fecha={fecha:%Y-%m-%d}&tab={tab}&q=",
            "hint": "Completar N° Guía",
        })
    if sin_factura:
        alertas.append({
            "label": "Registros sin factura",
            "count": sin_factura,
            "level": "warning",
            "href": f"?fecha={fecha:%Y-%m-%d}&tab={tab}&q=",
            "hint": "Completar N° Factura",
        })
    if sin_viaje:
        alertas.append({
            "label": "Registros sin viaje",
            "count": sin_viaje,
            "level": "info",
            "href": f"?fecha={fecha:%Y-%m-%d}&tab={tab}&q=",
            "hint": "Completar referencia viaje",
        })
    if sin_monto:
        alertas.append({
            "label": "Registros sin monto",
            "count": sin_monto,
            "level": "danger",
            "href": f"?fecha={fecha:%Y-%m-%d}&tab={tab}&q=",
            "hint": "Completar monto",
        })
    if urgentes_pend:
        alertas.append({
            "label": "Urgentes pendientes",
            "count": urgentes_pend,
            "level": "danger",
            "href": f"?fecha={fecha:%Y-%m-%d}&tab={getattr(EstadoRegistro, 'PENDIENTE', 'PEND')}&q=",
            "hint": "Revisar urgencias",
        })

    context = {
        "fecha": fecha,
        "tab": tab,
        "q": q,
        "registros": registros,
        "conteos": conteos,
        "total_monto": total_monto,
        "estados": EstadoRegistro.choices,

        # Panel PRO++
        "total_registros": total_registros,
        "pendientes": pendientes,
        "en_proceso": en_proceso,
        "completados": completados,
        "cancelados": cancelados,

        # Alertas PRO+++
        "alertas": alertas,
    }
    return render(request, "operaciones/tablero_diario.html", context)


# ------------------------------------------------------------
# Crear rápido
# ------------------------------------------------------------

@login_required
@permission_required("operaciones.puede_editar_estado", raise_exception=True)
@transaction.atomic
def crear_rapido(request):
    if request.method != "POST":
        return redirect("operaciones:tablero_diario")

    fecha = _parse_fecha(request.POST.get("fecha") or str(timezone.localdate()))

    corr = EstadoFacturacionGuia.siguiente_correlativo(fecha)
    obj = EstadoFacturacionGuia.objects.create(
        fecha=fecha,
        correlativo_diario=corr,
        creado_por=request.user,
        actualizado_por=request.user,
        estado=EstadoRegistro.PENDIENTE,
    )

    messages.success(request, f"Registro creado: {obj}")

    next_url = (request.POST.get("next") or "").strip()

    # 🔒 Blindaje: si next viene como ?fecha=...
    if next_url.startswith("?"):
        base = reverse("operaciones:tablero_diario")
        next_url = f"{base}{next_url}"

    # ✅ Agregamos open=<id> para abrir modal automáticamente
    if next_url:
        sep = "&" if "?" in next_url else "?"
        return redirect(f"{next_url}{sep}open={obj.id}")

    base = reverse("operaciones:tablero_diario")
    qs = urlencode(
        {"fecha": fecha.isoformat(), "tab": EstadoRegistro.PENDIENTE, "open": obj.id}
    )
    return redirect(f"{base}?{qs}")


# ------------------------------------------------------------
# Detalle / Lock / Unlock / Guardar
# ------------------------------------------------------------

@login_required
@permission_required("operaciones.puede_editar_estado", raise_exception=True)
def registro_detalle_json(request, pk):
    obj = get_object_or_404(EstadoFacturacionGuia, pk=pk)

    data = {
        "id": obj.id,
        "fecha": obj.fecha.isoformat(),
        "correlativo": obj.correlativo_diario,
        "cliente": obj.cliente_id,
        "origen": obj.origen_id,
        "destino": obj.destino_id,
        "nro_guia": obj.nro_guia or "",
        "nro_factura": obj.nro_factura or "",
        "referencia_viaje": obj.referencia_viaje or "",
        "monto": str(obj.monto) if obj.monto is not None else "",
        "estado": obj.estado,
        "prioridad": obj.prioridad,
        "observaciones": obj.observaciones or "",
        "bloqueado_por": _user_label(obj.bloqueado_por) if obj.bloqueado_por else "",
        "bloqueado": bool(obj.esta_bloqueado() and not obj.bloqueo_expirado()),
    }
    return JsonResponse({"ok": True, "data": data})


@login_required
@permission_required("operaciones.puede_editar_estado", raise_exception=True)
@transaction.atomic
def registro_lock(request, pk):
    obj = get_object_or_404(EstadoFacturacionGuia, pk=pk)

    if obj.esta_bloqueado() and not obj.bloqueo_expirado() and obj.bloqueado_por_id != request.user.id:
        return JsonResponse(
            {"ok": False, "msg": f"Registro bloqueado: lo está editando {_user_label(obj.bloqueado_por)}"},
            status=409,
        )

    obj.bloquear(request.user)
    obj.save(update_fields=["bloqueado_por", "bloqueado_desde"])
    return JsonResponse({"ok": True})


@login_required
@permission_required("operaciones.puede_editar_estado", raise_exception=True)
@transaction.atomic
def registro_unlock(request, pk):
    obj = get_object_or_404(EstadoFacturacionGuia, pk=pk)

    if obj.bloqueado_por_id != request.user.id and not request.user.has_perm("operaciones.puede_desbloquear_estado"):
        return HttpResponseForbidden("No puedes desbloquear este registro.")

    obj.desbloquear()
    obj.save(update_fields=["bloqueado_por", "bloqueado_desde"])
    return JsonResponse({"ok": True})


@login_required
@permission_required("operaciones.puede_editar_estado", raise_exception=True)
@transaction.atomic
def registro_guardar(request, pk):
    obj = get_object_or_404(EstadoFacturacionGuia, pk=pk)

    if not obj.puede_editar(request.user):
        owner = _user_label(obj.bloqueado_por) if obj.bloqueado_por else "otro usuario"
        return JsonResponse(
            {"ok": False, "msg": f"Registro bloqueado: lo está editando {owner}. Intenta nuevamente en un momento."},
            status=409,
        )

    if request.method != "POST":
        return JsonResponse({"ok": False, "msg": "Método inválido."}, status=405)

    form = EstadoFacturacionGuiaForm(request.POST, instance=obj)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.actualizado_por = request.user

        # mantiene el bloqueo vivo para el usuario que guarda
        obj.bloquear(request.user)
        obj.save()
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


# ------------------------------------------------------------
# Heartbeat (mantener bloqueo vivo mientras modal está abierto)
# ------------------------------------------------------------

@login_required
@permission_required("operaciones.puede_editar_estado", raise_exception=True)
@require_POST
@transaction.atomic
def registro_heartbeat(request, pk):
    obj = get_object_or_404(EstadoFacturacionGuia, pk=pk)

    if obj.esta_bloqueado() and not obj.bloqueo_expirado() and obj.bloqueado_por_id != request.user.id:
        return JsonResponse({"ok": False, "msg": f"Editando: {_user_label(obj.bloqueado_por)}"}, status=409)

    obj.bloquear(request.user)
    obj.save(update_fields=["bloqueado_por", "bloqueado_desde"])
    return JsonResponse({"ok": True})


# ------------------------------------------------------------
# Presencia multiusuario (cache)
# ------------------------------------------------------------

def _pres_key(fecha, user_id):
    return f"ops:pres:{fecha.isoformat()}:{user_id}"


@login_required
@permission_required("operaciones.puede_ver_estado", raise_exception=True)
@require_POST
def presencia_ping(request):
    fecha = _parse_fecha(request.POST.get("fecha") or "")
    tab = (request.POST.get("tab") or "").strip()

    payload = {
        "user_id": request.user.id,
        "name": _user_label(request.user),
        "tab": tab,
        "ts": timezone.now().isoformat(),
    }

    # marca presencia (si deja de pinguear, desaparece)
    cache.set(_pres_key(fecha, request.user.id), payload, timeout=35)

    # mantenemos un listado de IDs vistos en el día (mejor usar LIST que set por compatibilidad)
    seen_ids_key = f"ops:pres:ids:{fecha.isoformat()}"
    ids = cache.get(seen_ids_key) or []
    if request.user.id not in ids:
        ids.append(request.user.id)
    cache.set(seen_ids_key, ids, timeout=60 * 60)

    return JsonResponse({"ok": True})


@login_required
@permission_required("operaciones.puede_ver_estado", raise_exception=True)
@require_GET
def presencia_lista(request):
    fecha = _parse_fecha(request.GET.get("fecha") or "")
    seen_ids_key = f"ops:pres:ids:{fecha.isoformat()}"
    ids = cache.get(seen_ids_key) or []

    conectados = []
    for uid in ids:
        p = cache.get(_pres_key(fecha, uid))
        if p:
            conectados.append({"id": p.get("user_id"), "name": p.get("name"), "tab": p.get("tab", "")})

    # editando desde DB (bloqueos vivos)
    editando = []
    qs = EstadoFacturacionGuia.objects.select_related("bloqueado_por").filter(fecha=fecha)
    for obj in qs:
        if obj.bloqueado_por_id and obj.esta_bloqueado() and not obj.bloqueo_expirado():
            editando.append({
                "id": obj.id,
                "user_id": obj.bloqueado_por_id,
                "user_name": _user_label(obj.bloqueado_por),
                "correlativo": obj.correlativo_diario,
                "tab": obj.estado,
            })
            # de paso, garantizamos que ese user salga en ids
            if obj.bloqueado_por_id not in ids:
                ids.append(obj.bloqueado_por_id)

    cache.set(seen_ids_key, ids, timeout=60 * 60)

    return JsonResponse({"ok": True, "conectados": conectados, "editando": editando})


# ------------------------------------------------------------
# Auto-refresh liviano (KPIs + bloqueo filas visibles)
# ------------------------------------------------------------

@login_required
@permission_required("operaciones.puede_ver_estado", raise_exception=True)
@require_GET
def tablero_refresh(request):
    fecha = _parse_fecha(request.GET.get("fecha") or "")
    tab = (request.GET.get("tab") or EstadoRegistro.PENDIENTE).strip()
    q = (request.GET.get("q") or "").strip()

    ids_str = (request.GET.get("ids") or "").strip()
    ids = []
    if ids_str:
        try:
            ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
        except Exception:
            ids = []

    base_qs = _base_qs_por_fecha_y_q(fecha, q)

    conteos = dict(
        base_qs.values("estado").annotate(c=Count("id")).values_list("estado", "c")
    )
    total_monto = base_qs.aggregate(total=Sum("monto"))["total"] or 0

    filas = {}
    if ids:
        qs = base_qs.filter(id__in=ids).select_related("cliente", "origen", "destino", "bloqueado_por")
        for obj in qs:
            bloqueado = bool(obj.bloqueado_por_id and obj.esta_bloqueado() and not obj.bloqueo_expirado())
            filas[str(obj.id)] = {
                "id": obj.id,
                "correlativo": obj.correlativo_diario,
                "cliente_nombre": str(obj.cliente) if obj.cliente_id else "-",
                "origen_nombre": str(obj.origen) if obj.origen_id else "-",
                "destino_nombre": str(obj.destino) if obj.destino_id else "-",
                "nro_guia": obj.nro_guia or "",
                "nro_factura": obj.nro_factura or "",
                "referencia_viaje": obj.referencia_viaje or "",
                "monto": str(obj.monto) if obj.monto is not None else "",
                "estado": obj.estado,
                "prioridad": obj.prioridad,
                "bloqueado": bloqueado,
                "bloqueado_por": _user_label(obj.bloqueado_por) if obj.bloqueado_por_id else "",
                "es_tab_actual": (obj.estado == tab),
            }

    return JsonResponse({
        "ok": True,
        "conteos": conteos,
        "total_monto": str(total_monto),
        "filas": filas,
        "server_time": timezone.now().isoformat(),
    })


# ============================================================
# Estatus de Viajes (AM/PM) - reemplazo planilla Excel (Opción A)
# ============================================================

@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
def estatus_viajes_panel(request):
    hoy = timezone.localdate()
    fecha = _parse_fecha(request.GET.get("fecha")) or hoy
    turno = request.GET.get("turno") or "TODOS"
    q = (request.GET.get("q") or "").strip()

    qs = EstatusOperacionalViaje.objects.select_related("conductor", "tracto", "rampla").filter(fecha=fecha)

    if turno in [TurnoEstatus.AM, TurnoEstatus.PM]:
        qs = qs.filter(turno=turno)

    if q:
        qs = qs.filter(
            models.Q(conductor__nombres__icontains=q)
            | models.Q(conductor__apellidos__icontains=q)
            | models.Q(conductor__rut__icontains=q)
            | models.Q(tracto__patente__icontains=q)
            | models.Q(rampla__patente__icontains=q)
            | models.Q(estado_texto__icontains=q)
        )

    qs = qs.order_by("conductor__apellidos", "conductor__nombres", "turno")

    form = EstatusOperacionalViajeForm(initial={
        "fecha": fecha,
        "turno": TurnoEstatus.AM if turno == "TODOS" else turno
    })

    return render(request, "operaciones/estatus_viajes.html", {
        "fecha": fecha,
        "turno": turno,
        "q": q,
        "items": qs,
        "form": form,
        "turnos": ["TODOS", TurnoEstatus.AM, TurnoEstatus.PM],
    })


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
def estatus_viajes_guardar(request):
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
                "estado_texto": d.get("estado_texto"),
                "creado_por": request.user,
                "actualizado_por": request.user,
            },
        )

        if not created:
            obj.tracto = d.get("tracto")
            obj.rampla = d.get("rampla")
            obj.estado_texto = d.get("estado_texto")
            obj.actualizado_por = request.user
            obj.save()

    messages.success(request, "Estatus guardado ✅")
    return redirect(_estatus_redirect(request))


@login_required
@permission_required("operaciones.puede_editar_estatus_viajes", raise_exception=True)
@require_POST
def estatus_viajes_eliminar(request, pk: int):
    obj = get_object_or_404(EstatusOperacionalViaje, pk=pk)
    obj.delete()
    messages.success(request, "Estatus eliminado.")
    return redirect(_estatus_redirect(request))


@login_required
@permission_required("operaciones.puede_ver_estatus_viajes", raise_exception=True)
@require_GET
def estatus_viajes_export(request):
    import csv
    from django.http import HttpResponse

    hoy = timezone.localdate()
    fecha = _parse_fecha(request.GET.get("fecha")) or hoy
    turno = request.GET.get("turno") or "TODOS"
    q = (request.GET.get("q") or "").strip()

    qs = EstatusOperacionalViaje.objects.select_related("conductor", "tracto", "rampla").filter(fecha=fecha)

    if turno in [TurnoEstatus.AM, TurnoEstatus.PM]:
        qs = qs.filter(turno=turno)

    if q:
        qs = qs.filter(
            models.Q(conductor__nombres__icontains=q)
            | models.Q(conductor__apellidos__icontains=q)
            | models.Q(conductor__rut__icontains=q)
            | models.Q(tracto__patente__icontains=q)
            | models.Q(rampla__patente__icontains=q)
            | models.Q(estado_texto__icontains=q)
        )

    qs = qs.order_by("conductor__apellidos", "conductor__nombres", "turno")

    filename = f"estatus_viajes_{fecha.strftime('%Y%m%d')}_{turno if turno!='TODOS' else 'ALL'}.csv"
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(resp)
    writer.writerow(["Fecha", "Turno", "Chofer", "RUT", "Tracto", "Rampla", "Estado", "Actualizado"])

    for r in qs:
        writer.writerow([
            r.fecha.strftime("%d-%m-%Y"),
            r.turno,
            f"{r.conductor.nombres} {r.conductor.apellidos}",
            r.conductor.rut,
            getattr(r.tracto, "patente", "") or "",
            getattr(r.rampla, "patente", "") or "",
            (r.estado_texto or "").strip(),
            timezone.localtime(r.actualizado_el).strftime("%d-%m-%Y %H:%M"),
        ])

    return resp


def _turnos_a_mostrar(turno_param: str):
    turno_param = (turno_param or "TODOS").upper()
    if turno_param in [TurnoEstatus.AM, TurnoEstatus.PM]:
        return [turno_param]
    return [TurnoEstatus.AM, TurnoEstatus.PM]


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
            models.Q(conductor__nombres__icontains=q) |
            models.Q(conductor__apellidos__icontains=q) |
            models.Q(conductor__rut__icontains=q) |
            models.Q(tracto__patente__icontains=q) |
            models.Q(rampla__patente__icontains=q) |
            models.Q(estado_texto__icontains=q)
        )

    # ✅ choferes faltantes
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
            models.Q(conductor__nombres__icontains=q) |
            models.Q(conductor__apellidos__icontains=q) |
            models.Q(conductor__rut__icontains=q) |
            models.Q(tracto__patente__icontains=q) |
            models.Q(rampla__patente__icontains=q) |
            models.Q(estado_texto__icontains=q)
        )

    try:
        from openpyxl import Workbook
    except Exception:
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