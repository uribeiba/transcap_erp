from pyexpat.errors import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.forms import inlineformset_factory

from .forms import (
    ClienteForm,
    CotizacionForm,
    CotizacionItemFormSet,
    CotizacionItemFormSetEdit,
    CotizacionCuotaFormSet,
)
from .models import (
    Cliente,
    Cotizacion,
    CotizacionEstado,
    Vendedor,
    CotizacionItem,
    CotizacionCuota,
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _is_ajax(request):
    """Detecta si la petición es AJAX"""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _parse_date(date_str: str):
    s = (date_str or "").strip()
    if not s:
        return None
    try:
        return timezone.datetime.fromisoformat(s).date()
    except Exception:
        return None


# ============================================================
# HOME
# ============================================================
@login_required
def centro_home(request):
    return render(request, "centro_comercio/home.html")


# ============================================================
# CLIENTES
# ============================================================
@login_required
def clientes_panel(request):
    return render(request, "centro_comercio/clientes/panel.html")


@login_required
@require_GET
def clientes_lista(request):
    q = (request.GET.get("q") or "").strip()
    qs = Cliente.objects.all().order_by("razon_social")
    if q:
        qs = qs.filter(
            Q(razon_social__icontains=q)
            | Q(rut__icontains=q)
            | Q(giro__icontains=q)
            | Q(email__icontains=q)
            | Q(telefono__icontains=q)
        )
    return render(
        request,
        "centro_comercio/clientes/_tabla.html",
        {"clientes": qs, "q": q},
    )


@login_required
def cliente_detalle(request, pk: int):
    obj = get_object_or_404(Cliente, pk=pk)
    return render(request, "centro_comercio/clientes/_detalle.html", {"c": obj})


@login_required
def cliente_form(request, pk: int = None):
    obj = get_object_or_404(Cliente, pk=pk) if pk else None
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=obj)
        if form.is_valid():
            saved = form.save()
            if _is_ajax(request):
                return JsonResponse({"ok": True, "id": saved.id})
            return redirect(
                f"{reverse('centro_comercio:clientes_panel')}?open={saved.id}"
            )
        if _is_ajax(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return render(
            request,
            "centro_comercio/clientes/_form.html",
            {"form": form, "obj": obj},
            status=400,
        )
    form = ClienteForm(instance=obj)
    return render(
        request,
        "centro_comercio/clientes/_form.html",
        {"form": form, "obj": obj},
    )


@login_required
@require_POST
def cliente_eliminar(request, pk: int):
    """Elimina un cliente verificando que no tenga registros relacionados"""
    obj = get_object_or_404(Cliente, pk=pk)
    try:
        obj.delete()
        return JsonResponse({"ok": True, "message": "Cliente eliminado correctamente"})
    except ProtectedError as e:
        # Obtener los nombres de los modelos relacionados
        relacionados = []
        for related in e.protected_objects:
            model_name = related._meta.verbose_name
            if hasattr(related, "razon_social"):
                identificador = related.razon_social
            elif hasattr(related, "codigo"):
                identificador = related.codigo
            else:
                identificador = str(related.id)
            relacionados.append(f"{model_name} '{identificador}'")

        mensaje = (
            f"No se puede eliminar el cliente porque tiene registros relacionados: "
            f"{', '.join(relacionados)}. Desactive el cliente en lugar de eliminarlo."
        )
        return JsonResponse({"ok": False, "error": mensaje}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ============================================================
# VENDEDORES
# ============================================================
@login_required
@require_GET
def vendedores_lista_api(request):
    q = (request.GET.get("q") or "").strip()
    qs = Vendedor.objects.filter(activo=True)
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(email__icontains=q))
    data = [
        {
            "id": v.id,
            "text": f"{v.nombre} - {v.comision_porcentaje}%",
            "comision": str(v.comision_porcentaje),
        }
        for v in qs[:20]
    ]
    return JsonResponse({"results": data})


# ============================================================
# COTIZACIONES
# ============================================================
@login_required
def cotizaciones_panel(request):
    return render(request, "centro_comercio/cotizaciones/panel.html")


@login_required
@require_GET
def cotizaciones_lista(request):
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip()
    fecha_str = (
        request.GET.get("fecha") or request.GET.get("fecha_cotizacion") or ""
    ).strip()
    fecha = _parse_date(fecha_str)
    qs = Cotizacion.objects.select_related("cliente", "vendedor").all()
    if estado in dict(CotizacionEstado.choices):
        qs = qs.filter(estado=estado)
    if fecha:
        qs = qs.filter(fecha=fecha)
    if q:
        qs = qs.filter(
            Q(codigo__icontains=q)
            | Q(cliente__razon_social__icontains=q)
            | Q(cliente__rut__icontains=q)
            | Q(glosa__icontains=q)
        )
    qs = qs.order_by("-id")
    return render(
        request,
        "centro_comercio/cotizaciones/_tabla.html",
        {
            "cotizaciones": qs,
            "q": q,
            "estado": estado,
            "estados": CotizacionEstado.choices,
            "fecha": fecha_str,
        },
    )


@login_required
def cotizacion_detalle(request, pk: int):
    obj = get_object_or_404(
        Cotizacion.objects.select_related("cliente", "vendedor").prefetch_related(
            "items", "cuotas"
        ),
        pk=pk,
    )
    return render(request, "centro_comercio/cotizaciones/_detalle.html", {"c": obj})


@login_required
def cotizacion_form(request, pk: int = None):
    """
    Formulario para crear/editar cotización - CON CUOTAS INCLUIDAS
    """
    obj = get_object_or_404(Cotizacion, pk=pk) if pk else None

    if request.method == "POST":
        # Usar formset con extra=0 para evitar problemas
        if obj:
            formset = CotizacionItemFormSetEdit(
                request.POST, request.FILES, instance=obj, prefix="items"
            )
        else:
            formset = CotizacionItemFormSet(
                request.POST, request.FILES, instance=obj, prefix="items"
            )

        # Formset de cuotas
        cuota_formset = CotizacionCuotaFormSet(
            request.POST, instance=obj, prefix="cuotas"
        )

        # Formulario principal
        form = CotizacionForm(request.POST, instance=obj, user=request.user)

        # Validar todo junto
        if form.is_valid() and formset.is_valid() and cuota_formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar cabecera
                    cot = form.save(commit=False)

                    cot.descuento = cot.descuento or 0
                    cot.descuento_porcentaje = cot.descuento_porcentaje or 0
                    cot.recargo_porcentaje = cot.recargo_porcentaje or 0
                    cot.comision_porcentaje = cot.comision_porcentaje or 0

                    # Generar código si no existe
                    if (
                        not cot.codigo
                        or cot.codigo.strip() == ""
                        or cot.codigo == "Se generará automáticamente"
                    ):
                        cot.codigo = ""  # el modelo lo generará

                    cot.save()

                    # Guardar items
                    instances = formset.save(commit=False)
                    for instance in instances:
                        titulo = (instance.titulo or "").strip()
                        if titulo:
                            instance.cotizacion = cot
                            instance.save()

                    # Eliminar items marcados
                    for obj_del in formset.deleted_objects:
                        obj_del.delete()

                    # Guardar cuotas
                    cuota_instances = cuota_formset.save(commit=False)
                    for cuota in cuota_instances:
                        cuota.cotizacion = cot
                        cuota.save()

                    # Eliminar cuotas marcadas
                    for cuota_del in cuota_formset.deleted_objects:
                        cuota_del.delete()

                    if _is_ajax(request):
                        return JsonResponse({"ok": True, "id": cot.id})

                    return redirect(
                        f"{reverse('centro_comercio:cotizaciones_panel')}?open={cot.id}"
                    )

            except Exception as e:
                if _is_ajax(request):
                    return JsonResponse({"ok": False, "error": str(e)}, status=500)
                raise e

        # Errores de validación
        if _is_ajax(request):
            errors = {}
            if form.errors:
                errors["form"] = form.errors
            if formset.errors:
                errors["formset_items"] = formset.errors
            if cuota_formset.errors:
                errors["formset_cuotas"] = cuota_formset.errors
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        return render(
            request,
            "centro_comercio/cotizaciones/_form.html",
            {
                "form": form,
                "formset": formset,
                "cuota_formset": cuota_formset,
                "obj": obj,
            },
            status=400,
        )

    # -------------------------
    # GET
    # -------------------------
    if obj is None:
        form = CotizacionForm(
            initial={
                "sucursal": "MATRIZ",
                "fecha": timezone.localdate(),
                "vigencia_hasta": timezone.localdate(),
                "descuento": 0,
                "descuento_porcentaje": 0,
                "recargo_porcentaje": 0,
                "codigo": "",
                "condicion_venta": "CRED",
            },
            user=request.user,
        )
        formset = CotizacionItemFormSet(instance=None, prefix="items")
        cuota_formset = CotizacionCuotaFormSet(instance=None, prefix="cuotas")
    else:
        form = CotizacionForm(instance=obj, user=request.user)
        formset = CotizacionItemFormSetEdit(instance=obj, prefix="items")
        cuota_formset = CotizacionCuotaFormSet(instance=obj, prefix="cuotas")

    return render(
        request,
        "centro_comercio/cotizaciones/_form.html",
        {
            "form": form,
            "formset": formset,
            "cuota_formset": cuota_formset,
            "obj": obj,
        },
    )


@login_required
@require_POST
def cotizacion_eliminar(request, pk: int):
    """Elimina una cotización solo si está en estado Pendiente"""
    obj = get_object_or_404(Cotizacion, pk=pk)
    
    # Solo permitir eliminar si está Pendiente
    if obj.estado == CotizacionEstado.PENDIENTE:
        obj.delete()
        if _is_ajax(request):
            return JsonResponse({"ok": True, "message": "Cotización eliminada correctamente."})
        messages.success(request, "Cotización eliminada correctamente.")
        return redirect('centro_comercio:cotizaciones_panel')
    elif obj.estado == CotizacionEstado.ACEPTADA:
        if _is_ajax(request):
            return JsonResponse({"ok": False, "error": "No se puede eliminar una cotización aceptada. Solo puede anularla."}, status=400)
        messages.error(request, "No se puede eliminar una cotización aceptada. Solo puede anularla.")
    elif obj.estado == CotizacionEstado.ANULADA:
        if _is_ajax(request):
            return JsonResponse({"ok": False, "error": "No se puede eliminar una cotización anulada. Déjala como registro histórico."}, status=400)
        messages.error(request, "No se puede eliminar una cotización anulada. Déjala como registro histórico.")
    
    return redirect('centro_comercio:cotizaciones_panel')


@login_required
@require_GET
def cotizacion_cliente_info(request, cliente_id: int):
    cliente = get_object_or_404(Cliente, pk=cliente_id, activo=True)
    data = {
        "id": cliente.id,
        "rut": cliente.rut,
        "razon_social": cliente.razon_social,
        "giro": cliente.giro,
        "telefono": cliente.telefono,
        "email": cliente.email,
        "direccion": cliente.direccion,
        "localidad": cliente.localidad,
    }
    return JsonResponse(data)


@login_required
@require_GET
def cotizacion_resumen_api(request, pk: int):
    obj = get_object_or_404(
        Cotizacion.objects.select_related("cliente", "vendedor").prefetch_related(
            "items"
        ),
        pk=pk,
    )
    items_data = []
    for it in obj.items.all():
        items_data.append(
            {
                "id": it.id,
                "titulo": it.titulo,
                "unidad": it.unidad,
                "cantidad": str(it.cantidad),
                "valor_unitario": str(it.valor_unitario),
                "exento": it.exento,
                "descuento_porcentaje": str(it.descuento_porcentaje),
                "descuento": str(it.descuento),
                "total": str(it.total),
            }
        )
    data = {
        "id": obj.id,
        "codigo": obj.codigo,
        "cliente": {
            "id": obj.cliente.id,
            "razon_social": obj.cliente.razon_social,
            "rut": obj.cliente.rut,
        },
        "fecha": obj.fecha.isoformat(),
        "vigencia_hasta": obj.vigencia_hasta.isoformat(),
        "sucursal": obj.sucursal,
        "vendedor": {
            "id": obj.vendedor.id,
            "nombre": obj.vendedor.nombre,
        }
        if obj.vendedor
        else None,
        "comision_porcentaje": str(obj.comision_porcentaje),
        "descuento_porcentaje": str(obj.descuento_porcentaje),
        "descuento": str(obj.descuento),
        "recargo_porcentaje": str(obj.recargo_porcentaje),
        "glosa": obj.glosa,
        "observaciones": obj.observaciones,
        "terminos": obj.terminos,
        "estado": obj.estado,
        "estado_display": obj.get_estado_display(),
        "totales": {
            "subtotal": str(obj.subtotal),
            "total_afecto": str(obj.total_afecto),
            "total_exento": str(obj.total_exento),
            "iva": str(obj.iva),
            "descuento_aplicado": str(obj.descuento_aplicado),
            "recargo_aplicado": str(obj.recargo_aplicado),
            "total_neto": str(obj.total_neto),
        },
        "items": items_data,
    }
    return JsonResponse(data)


@login_required
@require_POST
def cotizacion_duplicar(request, pk: int):
    original = get_object_or_404(Cotizacion, pk=pk)
    with transaction.atomic():
        nueva = Cotizacion(
            cliente=original.cliente,
            sucursal=original.sucursal,
            vendedor=original.vendedor,
            comision_porcentaje=original.comision_porcentaje,
            fecha=timezone.localdate(),
            vigencia_hasta=timezone.localdate(),
            descuento_porcentaje=original.descuento_porcentaje,
            descuento=original.descuento,
            recargo_porcentaje=original.recargo_porcentaje,
            glosa=original.glosa,
            observaciones=original.observaciones,
            terminos=original.terminos,
            condicion_venta=original.condicion_venta,
            estado=CotizacionEstado.PENDIENTE,
        )
        nueva.save()

        for item in original.items.all():
            CotizacionItem.objects.create(
                cotizacion=nueva,
                titulo=item.titulo,
                unidad=item.unidad,
                cantidad=item.cantidad,
                valor_unitario=item.valor_unitario,
                exento=item.exento,
                descuento_porcentaje=item.descuento_porcentaje,
                descuento=item.descuento,
            )

        for cuota in original.cuotas.all():
            CotizacionCuota.objects.create(
                cotizacion=nueva,
                fecha=cuota.fecha,
                monto=cuota.monto,
            )

    if _is_ajax(request):
        return JsonResponse({"ok": True, "id": nueva.id})
    return redirect(
        f"{reverse('centro_comercio:cotizaciones_panel')}?open={nueva.id}"
    )


@login_required
@require_POST
def cotizacion_cambiar_estado(request, pk: int):
    obj = get_object_or_404(Cotizacion, pk=pk)
    nuevo_estado = request.POST.get("estado")
    if nuevo_estado in dict(CotizacionEstado.choices):
        obj.estado = nuevo_estado
        obj.save()
        return JsonResponse({"ok": True, "estado": obj.get_estado_display()})
    return JsonResponse({"ok": False, "error": "Estado inválido"}, status=400)


# ============================================================
# PDF - GENERAR DOCUMENTO
# ============================================================
@login_required
def cotizacion_pdf(request, pk: int):
    """Generar PDF de la cotización"""
    obj = get_object_or_404(
        Cotizacion.objects.select_related("cliente", "vendedor").prefetch_related(
            "items", "cuotas"
        ),
        pk=pk,
    )
    return render(
        request,
        "centro_comercio/cotizaciones/cotizacion_pdf.html",
        {"cotizacion": obj},
    )