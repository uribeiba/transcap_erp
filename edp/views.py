from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.template.loader import get_template

from bitacora.models import Bitacora
from .models import EDP, EDPServicio, EDPago
from .forms import EDPForm, ServiciosSelectForm, EDPPagoFormSet

STEPS = ["edp", "servicios", "pagos", "finalizar"]


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@login_required
def edp_panel(request):
    """
    Panel/listado de EDPs.
    """
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip()

    qs = EDP.objects.all().order_by("-created_at")

    if q:
        qs = qs.filter(codigo__icontains=q)

    if estado:
        qs = qs.filter(estado=estado)

    context = {
        "edps": qs,
        "q": q,
        "estado": estado,
    }
    return render(request, "edp/panel.html", context)


@login_required
def edp_wizard_new(request):
    """
    Crea un EDP mínimo y lo manda al paso 'edp'.
    """
    edp = EDP.objects.create()
    return redirect("edp:wizard", edp_id=edp.id, step="edp")


@login_required
def edp_wizard(request, edp_id: int, step: str):
    """
    Wizard: edp -> servicios -> pagos -> finalizar
    """
    if step not in STEPS:
        step = "edp"

    edp = get_object_or_404(EDP, pk=edp_id)

    # ---------- STEP 1: EDP ----------
    if step == "edp":
        if request.method == "POST":
            form = EDPForm(request.POST, instance=edp)
            if form.is_valid():
                form.save()
                messages.success(request, "EDP guardado.")
                if _is_ajax(request):
                    return JsonResponse({"ok": True, "id": edp.id, "next": "servicios"})
                return redirect("edp:wizard", edp_id=edp.id, step="servicios")
            else:
                if _is_ajax(request):
                    return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        else:
            form = EDPForm(instance=edp)

        return render(
            request,
            "edp/wizard.html",
            {
                "edp": edp,
                "step": step,
                "form": form,
                "items": edp.items.select_related("servicio", "servicio__cliente").all(),
                "pagos": edp.pagos.all(),
                "steps": STEPS,
            },
        )

    # ---------- STEP 2: SERVICIOS / BITÁCORA (CON FILTRO POR CLIENTE) ----------
    if step == "servicios":
        # 🔥 FILTRAR BITÁCORAS POR CLIENTE SELECCIONADO EN EL EDP
        bitacoras_qs = Bitacora.objects.select_related("cliente").all().order_by("-fecha", "-id")
        
        # Aplicar filtro por cliente si existe
        if edp.cliente:
            bitacoras_qs = bitacoras_qs.filter(cliente=edp.cliente)
        else:
            # Si no hay cliente seleccionado, mostrar lista vacía
            bitacoras_qs = bitacoras_qs.none()

        initial_selected = list(edp.items.values_list("servicio_id", flat=True))

        # Crear choices para el formulario
        choices_list = []
        for b in bitacoras_qs:
            cliente_nombre = b.cliente.razon_social if b.cliente else 'Sin cliente'
            origen = b.origen or '-'
            destino = b.destino or '-'
            fecha_str = b.fecha.strftime("%d/%m/%Y") if b.fecha else '--/--/----'
            choices_list.append(
                (b.id, f"BIT-{b.id} | {fecha_str} | {cliente_nombre} | {origen} → {destino}")
            )

        form = ServiciosSelectForm(
            choices=choices_list,
            initial={"servicios": initial_selected},
        )

        if request.method == "POST":
            # Reconstruir choices para el POST
            choices_list_post = []
            for b in bitacoras_qs:
                cliente_nombre = b.cliente.razon_social if b.cliente else 'Sin cliente'
                origen = b.origen or '-'
                destino = b.destino or '-'
                fecha_str = b.fecha.strftime("%d/%m/%Y") if b.fecha else '--/--/----'
                choices_list_post.append(
                    (b.id, f"BIT-{b.id} | {fecha_str} | {cliente_nombre} | {origen} → {destino}")
                )

            form = ServiciosSelectForm(
                request.POST,
                choices=choices_list_post,
            )

            if form.is_valid():
                selected_ids = [int(x) for x in (form.cleaned_data.get("servicios") or [])]

                with transaction.atomic():
                    # Eliminar servicios que ya no están seleccionados
                    edp.items.exclude(servicio_id__in=selected_ids).delete()

                    # Obtener IDs existentes
                    existing = set(edp.items.values_list("servicio_id", flat=True))
                    to_create = [sid for sid in selected_ids if sid not in existing]

                    for sid in to_create:
                        bitacora = Bitacora.objects.get(pk=sid)

                        tarifa = Decimal("0")
                        if hasattr(bitacora, "tarifa_flete") and bitacora.tarifa_flete is not None:
                            tarifa = Decimal(bitacora.tarifa_flete or 0)
                        elif hasattr(bitacora, "total") and bitacora.total is not None:
                            tarifa = Decimal(bitacora.total or 0)

                        estadia = Decimal("0")
                        if hasattr(bitacora, "estadia") and bitacora.estadia is not None:
                            estadia = Decimal(bitacora.estadia or 0)

                        EDPServicio.objects.create(
                            edp=edp,
                            servicio=bitacora,
                            tarifa=tarifa,
                            estadia=estadia,
                        )

                    edp.recalcular_totales()

                messages.success(request, "Bitácoras asignadas al EDP correctamente.")
                if _is_ajax(request):
                    return JsonResponse({"ok": True, "id": edp.id, "next": "pagos"})
                return redirect("edp:wizard", edp_id=edp.id, step="pagos")
            else:
                if _is_ajax(request):
                    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        # Pasar información del cliente al template
        cliente_info = None
        if edp.cliente:
            cliente_info = {
                "nombre": edp.cliente.razon_social,
                "rut": edp.cliente.rut,
                "giro": edp.cliente.giro,
            }

        return render(
            request,
            "edp/wizard.html",
            {
                "edp": edp,
                "step": step,
                "form_servicios": form,
                "items": edp.items.select_related("servicio", "servicio__cliente").all(),
                "pagos": edp.pagos.all(),
                "steps": STEPS,
                "cliente_info": cliente_info,
                "total_bitacoras": bitacoras_qs.count(),
            },
        )

    # ---------- STEP 3: PAGOS (CON CONTROL DE ACCESO Y TRY/EXCEPT) ----------
    if step == "pagos":
        # 🔥 CONTROL DE ACCESO: Verificar si puede registrar pagos
        if edp.estado == 'BORR':
            messages.warning(request, "⚠️ El EDP está en estado 'Borrador'. Cambia el estado a 'En proceso' para poder registrar pagos.")
            return redirect("edp:wizard", edp_id=edp.id, step="edp")
        
        # Verificar si los pagos están deshabilitados (EDP pagado)
        pagos_disabled = edp.estado == 'PAGA'
        
        if request.method == "POST":
            # Si está pagado, no permitir modificar pagos
            if pagos_disabled:
                messages.error(request, "No se pueden modificar pagos de un EDP que ya está pagado.")
                return redirect("edp:wizard", edp_id=edp.id, step="finalizar")
            
            try:
                formset = EDPPagoFormSet(request.POST, instance=edp, prefix="pagos")
                
                # 🔥 DEBUG: Imprimir errores en consola para diagnóstico
                if not formset.is_valid():
                    print("=" * 50)
                    print("ERRORES EN FORMSET DE PAGOS:")
                    print(f"Total forms: {formset.total_form_count()}")
                    for i, form in enumerate(formset.forms):
                        if form.errors:
                            print(f"Form {i} errors: {form.errors}")
                    if formset.non_form_errors():
                        print(f"Non-form errors: {formset.non_form_errors()}")
                    print("=" * 50)
                
                if formset.is_valid():
                    with transaction.atomic():
                        # Guardar solo los forms que tienen monto > 0
                        instances = formset.save(commit=False)
                        for instance in instances:
                            if instance.monto and instance.monto > 0:
                                instance.save()
                        
                        # Eliminar los marcados para eliminar
                        for obj in formset.deleted_objects:
                            obj.delete()
                        
                        edp.recalcular_totales()
                        
                        # Si se registró al menos un pago y está en estado 'BORR', cambiar a 'PROC'
                        if edp.pagos.exists() and edp.estado == 'BORR':
                            edp.estado = 'PROC'
                            edp.save()
                            messages.info(request, "El EDP ha cambiado a estado 'En proceso' porque se registró al menos un pago.")
                    
                    messages.success(request, "Pagos guardados correctamente.")
                    if _is_ajax(request):
                        return JsonResponse({"ok": True, "id": edp.id, "next": "finalizar"})
                    return redirect("edp:wizard", edp_id=edp.id, step="finalizar")
                else:
                    # 🔥 Construir objeto de errores detallado para el frontend
                    errors_dict = {}
                    
                    for i, form in enumerate(formset.forms):
                        if form.errors:
                            errors_dict[f"pago_{i}"] = form.errors
                    
                    if formset.non_form_errors():
                        errors_dict["general"] = list(formset.non_form_errors())
                    
                    if not errors_dict:
                        errors_dict["error"] = "Error al validar los pagos. Verifique los montos y fechas."
                    
                    if _is_ajax(request):
                        return JsonResponse({"ok": False, "errors": errors_dict}, status=400)
                    
                    messages.error(request, "Error al guardar los pagos. Verifique los datos ingresados.")
            
            except Exception as e:
                print(f"ERROR EXCEPCIÓN EN PAGOS: {str(e)}")
                import traceback
                traceback.print_exc()
                
                if _is_ajax(request):
                    return JsonResponse({
                        "ok": False, 
                        "error": f"Error interno del servidor: {str(e)}"
                    }, status=500)
                raise e
        
        else:
            formset = EDPPagoFormSet(instance=edp, prefix="pagos")
        
        # Calcular total pagado y saldo pendiente
        total_pagado = sum(p.monto for p in edp.pagos.all()) if edp.pagos.exists() else Decimal('0')
        saldo_pendiente = edp.total - total_pagado

        return render(
            request,
            "edp/wizard.html",
            {
                "edp": edp,
                "step": step,
                "formset_pagos": formset,
                "items": edp.items.select_related("servicio", "servicio__cliente").all(),
                "pagos": edp.pagos.all(),
                "steps": STEPS,
                "pagos_disabled": pagos_disabled,
                "total_pagado": total_pagado,
                "saldo_pendiente": saldo_pendiente,
            },
        )

    # ---------- STEP 4: FINALIZAR ----------
    if step == "finalizar":
        return render(
            request,
            "edp/wizard.html",
            {
                "edp": edp,
                "step": step,
                "items": edp.items.select_related("servicio", "servicio__cliente").all(),
                "pagos": edp.pagos.all(),
                "steps": STEPS,
            },
        )


@login_required
def edp_detalle(request, edp_id: int):
    edp = get_object_or_404(EDP, pk=edp_id)
    return render(
        request,
        "edp/detalle.html",
        {
            "edp": edp,
            "items": edp.items.select_related("servicio", "servicio__cliente").all(),
            "pagos": edp.pagos.all(),
        },
    )


@login_required
@require_POST
def edp_eliminar(request, edp_id: int):
    edp = get_object_or_404(EDP, pk=edp_id)
    edp.delete()

    if _is_ajax(request):
        return JsonResponse({"ok": True})

    messages.success(request, "EDP eliminado.")
    return redirect("edp:panel")


# ============================================================
# PDF - GENERAR DOCUMENTO
# ============================================================
@login_required
def edp_pdf(request, edp_id: int):
    """
    Generar PDF del EDP - Formato profesional
    """
    edp = get_object_or_404(
        EDP.objects.select_related("cliente")
        .prefetch_related("items", "pagos"),
        pk=edp_id
    )
    
    return render(
        request, 
        "edp/edp_pdf.html", 
        {"edp": edp}
    )