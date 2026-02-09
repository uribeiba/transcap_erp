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

    conteos = dict(
        base_qs.values("estado").annotate(c=Count("id")).values_list("estado", "c")
    )
    total_monto = base_qs.aggregate(total=Sum("monto"))["total"] or 0

    registros = base_qs.filter(estado=tab).order_by("prioridad", "-id")[:400]

    context = {
        "fecha": fecha,
        "tab": tab,
        "q": q,
        "registros": registros,
        "conteos": conteos,
        "total_monto": total_monto,
        "estados": EstadoRegistro.choices,
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
