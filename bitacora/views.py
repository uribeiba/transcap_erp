from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from centro_comercio.models import Cliente
from taller.models import CoordinacionViaje

from .forms import BitacoraForm
from .models import Bitacora, EstadoBitacora


def _parse_iso_date(value):
    """
    Convierte 'YYYY-MM-DD' a date.
    Si viene vacío o inválido, devuelve None.
    """
    value = (value or "").strip()
    if not value:
        return None
    try:
        return timezone.datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def _initial_desde_estatus(request):
    """
    Construye valores iniciales para Bitácora a partir de query params
    enviados desde Operaciones -> Estatus de Viajes.
    """
    data = {}

    # IDs directos
    if request.GET.get("cliente"):
        data["cliente"] = request.GET.get("cliente")

    if request.GET.get("conductor"):
        data["conductor"] = request.GET.get("conductor")

    if request.GET.get("tracto"):
        data["tracto"] = request.GET.get("tracto")

    if request.GET.get("rampla"):
        data["rampla"] = request.GET.get("rampla")

    # Textos
    if request.GET.get("guias_raw"):
        data["guias_raw"] = request.GET.get("guias_raw")

    if request.GET.get("oc_edp_raw"):
        data["oc_edp_raw"] = request.GET.get("oc_edp_raw")

    if request.GET.get("origen"):
        data["origen"] = request.GET.get("origen")

    if request.GET.get("intermedio"):
        data["intermedio"] = request.GET.get("intermedio")

    if request.GET.get("destino"):
        data["destino"] = request.GET.get("destino")

    if request.GET.get("descripcion_trabajo"):
        data["descripcion_trabajo"] = request.GET.get("descripcion_trabajo")

    if request.GET.get("coordinador"):
        data["coordinador"] = request.GET.get("coordinador")

    # Fechas: convertir a date real para que type="date" las muestre bien
    fecha = _parse_iso_date(request.GET.get("fecha"))
    data["fecha"] = fecha or timezone.localdate()

    fecha_arribo = _parse_iso_date(request.GET.get("fecha_arribo"))
    if fecha_arribo:
        data["fecha_arribo"] = fecha_arribo

    fecha_descarga = _parse_iso_date(request.GET.get("fecha_descarga"))
    if fecha_descarga:
        data["fecha_descarga"] = fecha_descarga

    # Estado opcional
    if request.GET.get("estado"):
        data["estado"] = request.GET.get("estado")

    # Valores monetarios opcionales
    tarifa_flete = request.GET.get("tarifa_flete")
    if tarifa_flete not in [None, ""]:
        data["tarifa_flete"] = tarifa_flete

    estadia = request.GET.get("estadia")
    if estadia not in [None, ""]:
        data["estadia"] = estadia

    return data


def _selected_cliente_from_initial_or_instance(form=None, instance=None):
    """
    Devuelve el cliente seleccionado para poder usarlo en el template
    si hace falta mostrar resumen inicial.
    """
    if instance and getattr(instance, "cliente_id", None):
        return instance.cliente

    if form is not None:
        raw = form.initial.get("cliente")
        if raw:
            try:
                return Cliente.objects.filter(pk=raw).first()
            except Exception:
                return None
    return None


@login_required
def panel(request):
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip()

    qs = (
        Bitacora.objects.select_related(
            "cliente",
            "conductor",
            "tracto",
            "rampla",
            "coordinacion",
            "creado_por",
        )
        .all()
        .order_by("-fecha", "-id")
    )

    if q:
        filtros = (
            Q(cliente__razon_social__icontains=q)
            | Q(cliente__rut__icontains=q)
            | Q(origen__icontains=q)
            | Q(intermedio__icontains=q)
            | Q(destino__icontains=q)
            | Q(guias_raw__icontains=q)
            | Q(oc_edp_raw__icontains=q)
            | Q(coordinador__icontains=q)
            | Q(descripcion_trabajo__icontains=q)
        )
        if q.isdigit():
            filtros |= Q(id=int(q))
        qs = qs.filter(filtros)

    if estado:
        qs = qs.filter(estado=estado)

    context = {
        "bitacoras": qs,
        "q": q,
        "estado": estado,
        "estados": EstadoBitacora.choices,
    }
    return render(request, "bitacora/panel.html", context)


@login_required
def crear(request):
    """
    Crear bitácora manual o precargada desde Operaciones / Estatus de Viajes.
    """
    if request.method == "POST":
        form = BitacoraForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)

            if not getattr(obj, "creado_por_id", None):
                obj.creado_por = request.user

            if not obj.coordinador or obj.coordinador.strip() == "":
                obj.coordinador = request.user.get_full_name() or request.user.username

            obj.save()
            messages.success(request, "Bitácora creada correctamente.")
            return redirect("bitacora:panel")
    else:
        initial_data = _initial_desde_estatus(request)

        if not initial_data.get("coordinador"):
            initial_data["coordinador"] = request.user.get_full_name() or request.user.username

        if not initial_data.get("fecha"):
            initial_data["fecha"] = timezone.localdate()

        form = BitacoraForm(initial=initial_data, user=request.user)

    selected_cliente = _selected_cliente_from_initial_or_instance(form=form)

    return render(
        request,
        "bitacora/form.html",
        {
            "form": form,
            "selected_cliente": selected_cliente,
        },
    )


@login_required
def editar(request, pk):
    bitacora = get_object_or_404(Bitacora, pk=pk)

    if request.method == "POST":
        form = BitacoraForm(request.POST, instance=bitacora, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)

            if not obj.coordinador or obj.coordinador.strip() == "":
                obj.coordinador = request.user.get_full_name() or request.user.username

            obj.save()
            messages.success(request, "Bitácora actualizada correctamente.")
            return redirect("bitacora:panel")
    else:
        form = BitacoraForm(instance=bitacora, user=request.user)

    selected_cliente = _selected_cliente_from_initial_or_instance(instance=bitacora)

    return render(
        request,
        "bitacora/form.html",
        {
            "form": form,
            "bitacora": bitacora,
            "selected_cliente": selected_cliente,
        },
    )


@login_required
def detalle(request, pk):
    bitacora = get_object_or_404(
        Bitacora.objects.select_related(
            "cliente",
            "conductor",
            "tracto",
            "rampla",
            "coordinacion",
            "creado_por",
        ),
        pk=pk,
    )
    return render(request, "bitacora/detalle.html", {"bitacora": bitacora})


@login_required
@require_POST
def eliminar(request, pk):
    bitacora = get_object_or_404(Bitacora, pk=pk)
    bitacora.delete()
    messages.success(request, "Bitácora eliminada correctamente.")
    return redirect("bitacora:panel")


@login_required
def api_coordinacion_detalle(request, id):
    coord = get_object_or_404(CoordinacionViaje, pk=id)

    data = {
        "fecha_carga": coord.fecha_carga.isoformat() if coord.fecha_carga else "",
        "fecha_descarga": coord.fecha_descarga.isoformat() if coord.fecha_descarga else "",
        "origen": coord.origen or "",
        "intermedio": "",
        "destino": coord.destino or "",
        "tracto": coord.tracto_camion_id,
        "tracto_label": str(coord.tracto_camion) if coord.tracto_camion else "",
        "rampla": coord.semirremolque_id,
        "rampla_label": str(coord.semirremolque) if coord.semirremolque else "",
        "conductor": coord.conductor_id,
        "conductor_label": coord.conductor.nombre_completo if coord.conductor else "",
    }

    return JsonResponse(data)


@require_GET
def api_clientes(request):
    q = (request.GET.get("q") or "").strip()
    qs = Cliente.objects.all()

    if q:
        qs = qs.filter(
            models.Q(razon_social__icontains=q)
            | models.Q(rut__icontains=q)
        )

    qs = qs.order_by("razon_social")[:20]

    data = [
        {
            "id": c.id,
            "text": f"{c.razon_social} ({c.rut})",
            "razon_social": c.razon_social,
            "rut": c.rut,
            "giro": getattr(c, "giro", ""),
            "direccion": getattr(c, "direccion", ""),
            "localidad": getattr(c, "localidad", ""),
            "telefono": getattr(c, "telefono", ""),
            "email": getattr(c, "email", ""),
        }
        for c in qs
    ]
    return JsonResponse({"results": data})