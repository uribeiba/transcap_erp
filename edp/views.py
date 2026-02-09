# config/edp/views.py
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import EDP, EDPServicio, EDPago
from .forms import EDPForm, ServiciosSelectForm, EDPPagoFormSet

# CORRECCIÓN: Cambia esta línea
# from config.servicios.models import Servicio  # ❌ Incorrecto
from servicios.models import Servicio  # ✅ Correcto (app al mismo nivel)

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

    # Si lo cargas por fetch para una tabla parcial, puedes devolver un _tabla.html
    # Por ahora devolvemos panel normal.
    return render(request, "edp/panel.html", context)


# config/edp/views.py
@login_required
def edp_wizard_new(request):
    """
    Crea un EDP mínimo y lo manda al paso 'edp'.
    """
    # Crear EDP sin código (se generará automáticamente en el save)
    edp = EDP.objects.create()
    return redirect("edp:wizard", edp_id=edp.id, step="edp")


# config/edp/views.py - Solo la función edp_wizard actualizada

@login_required
def edp_wizard(request, edp_id: int, step: str):
    """
    Wizard: edp -> servicios -> pagos -> finalizar
    Compatible con modal (si lo llamas por fetch y devuelves HTML parcial).
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

        return render(request, "edp/wizard.html", {
            "edp": edp,
            "step": step,
            "form": form,
            "items": edp.items.select_related("servicio").all(),
            "pagos": edp.pagos.all(),
            "steps": STEPS,  # Agregar esto
        })

    # ---------- STEP 2: SERVICIOS (multi select) ----------
    if step == "servicios":
        # Choices: puedes mandar un listado de servicios (ej: activos) o todos
        servicios_qs = Servicio.objects.all().order_by("-id")

        # form con choices
        initial_selected = list(edp.items.values_list("servicio_id", flat=True))
        form = ServiciosSelectForm(
            choices=[(s.id, f"{getattr(s,'codigo','SERV')}-{s.id} — {str(s)}") for s in servicios_qs],
            initial={"servicios": initial_selected},
        )

        if request.method == "POST":
            form = ServiciosSelectForm(
                request.POST,
                choices=[(s.id, f"{getattr(s,'codigo','SERV')}-{s.id} — {str(s)}") for s in servicios_qs],
            )
            if form.is_valid():
                selected_ids = [int(x) for x in (form.cleaned_data.get("servicios") or [])]

                with transaction.atomic():
                    # Dejamos EXACTAMENTE los seleccionados: eliminamos los que ya no están
                    edp.items.exclude(servicio_id__in=selected_ids).delete()

                    # Creamos los nuevos
                    existing = set(edp.items.values_list("servicio_id", flat=True))
                    to_create = [sid for sid in selected_ids if sid not in existing]

                    for sid in to_create:
                        servicio = Servicio.objects.get(pk=sid)

                        # Si tu Servicio tiene campos "tarifa" o "precio", aquí puedes mapear.
                        # Si no existe, queda en 0.
                        tarifa = getattr(servicio, "tarifa", None) or getattr(servicio, "precio", None) or 0

                        EDPServicio.objects.create(
                            edp=edp,
                            servicio=servicio,
                            tarifa=Decimal(tarifa) if tarifa else Decimal("0"),
                            estadia=Decimal("0"),
                        )

                    # recalcula totales en el modelo
                    edp.recalcular_totales()

                messages.success(request, "Servicios asignados.")
                if _is_ajax(request):
                    return JsonResponse({"ok": True, "id": edp.id, "next": "pagos"})
                return redirect("edp:wizard", edp_id=edp.id, step="pagos")
            else:
                if _is_ajax(request):
                    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        return render(request, "edp/wizard.html", {
            "edp": edp,
            "step": step,
            "form_servicios": form,
            "items": edp.items.select_related("servicio").all(),
            "pagos": edp.pagos.all(),
            "steps": STEPS,  # Agregar esto
        })

    # ---------- STEP 3: PAGOS (inline formset) ----------
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

        return render(request, "edp/wizard.html", {
            "edp": edp,
            "step": step,
            "formset": formset,
            "items": edp.items.select_related("servicio").all(),
            "pagos": edp.pagos.all(),
            "steps": STEPS,  # Agregar esto
        })

    # ---------- STEP 4: FINALIZAR ----------
    if step == "finalizar":
        # Aquí podrías marcar edp.estado="PAG" si quieres finalizar real con botón
        return render(request, "edp/wizard.html", {
            "edp": edp,
            "step": step,
            "items": edp.items.select_related("servicio").all(),
            "pagos": edp.pagos.all(),
            "steps": STEPS,  # Agregar esto
        })


@login_required
def edp_detalle(request, edp_id: int):
    edp = get_object_or_404(EDP, pk=edp_id)
    return render(request, "edp/detalle.html", {
        "edp": edp,
        "items": edp.items.select_related("servicio").all(),
        "pagos": edp.pagos.all(),
    })


@login_required
@require_POST
def edp_eliminar(request, edp_id: int):
    edp = get_object_or_404(EDP, pk=edp_id)
    edp.delete()
    if _is_ajax(request):
        return JsonResponse({"ok": True})
    messages.success(request, "EDP eliminado.")
    return redirect("edp:panel")
