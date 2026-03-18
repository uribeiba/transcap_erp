from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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
    Mantiene el nombre del step 'servicios' por compatibilidad,
    pero ahora realmente trabaja con Bitácora como servicio operativo.
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

    # ---------- STEP 2: SERVICIOS / BITÁCORA ----------
    if step == "servicios":
        bitacoras_qs = (
            Bitacora.objects.select_related("cliente")
            .all()
            .order_by("-fecha", "-id")
        )

        initial_selected = list(edp.items.values_list("servicio_id", flat=True))

        form = ServiciosSelectForm(
            choices=[
                (
                    b.id,
                    f"BIT-{b.id} — "
                    f"{b.cliente.razon_social if b.cliente else 'Sin cliente'} — "
                    f"{b.origen or '-'} → {b.destino or '-'}"
                )
                for b in bitacoras_qs
            ],
            initial={"servicios": initial_selected},
        )

        if request.method == "POST":
            form = ServiciosSelectForm(
                request.POST,
                choices=[
                    (
                        b.id,
                        f"BIT-{b.id} — "
                        f"{b.cliente.razon_social if b.cliente else 'Sin cliente'} — "
                        f"{b.origen or '-'} → {b.destino or '-'}"
                    )
                    for b in bitacoras_qs
                ],
            )

            if form.is_valid():
                selected_ids = [int(x) for x in (form.cleaned_data.get("servicios") or [])]

                with transaction.atomic():
                    edp.items.exclude(servicio_id__in=selected_ids).delete()

                    existing = set(edp.items.values_list("servicio_id", flat=True))
                    to_create = [sid for sid in selected_ids if sid not in existing]

                    for sid in to_create:
                        bitacora = Bitacora.objects.get(pk=sid)

                        # Prioridad de tarifa:
                        # 1. tarifa_flete si existe
                        # 2. total si existe
                        # 3. 0
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
                "step_title": "Servicios / Bitácora",
            },
        )

    # ---------- STEP 3: PAGOS ----------
    if step == "pagos":
        if request.method == "POST":
            formset = EDPPagoFormSet(request.POST, instance=edp)
            if formset.is_valid():
                formset.save()
                edp.recalcular_totales()
                messages.success(request, "Pagos guardados.")
                if _is_ajax(request):
                    return JsonResponse({"ok": True, "id": edp.id, "next": "finalizar"})
                return redirect("edp:wizard", edp_id=edp.id, step="finalizar")
            else:
                if _is_ajax(request):
                    return JsonResponse({"ok": False, "errors": formset.errors}, status=400)
        else:
            formset = EDPPagoFormSet(instance=edp)

        return render(
            request,
            "edp/wizard.html",
            {
                "edp": edp,
                "step": step,
                "formset": formset,
                "items": edp.items.select_related("servicio", "servicio__cliente").all(),
                "pagos": edp.pagos.all(),
                "steps": STEPS,
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