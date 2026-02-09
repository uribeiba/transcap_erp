from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import ClienteForm, CotizacionForm, CotizacionItemFormSet
from .models import Cliente, Cotizacion, CotizacionEstado


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _parse_date(date_str: str):
    """
    Acepta 'YYYY-MM-DD'. Si viene vacío o inválido -> None.
    """
    s = (date_str or "").strip()
    if not s:
        return None
    try:
        return timezone.datetime.fromisoformat(s).date()
    except Exception:
        return None


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

            # ✅ AJAX -> JSON (modal)
            if _is_ajax(request):
                return JsonResponse({"ok": True, "id": saved.id})

            # ✅ normal -> volver al panel y abrir detalle
            return redirect(f"{reverse('centro_comercio:clientes_panel')}?open={saved.id}")

        # errores
        if _is_ajax(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        return render(
            request,
            "centro_comercio/clientes/_form.html",
            {"form": form, "obj": obj},
            status=400,
        )

    # GET
    form = ClienteForm(instance=obj)
    return render(request, "centro_comercio/clientes/_form.html", {"form": form, "obj": obj})


@login_required
@require_POST
def cliente_eliminar(request, pk: int):
    obj = get_object_or_404(Cliente, pk=pk)
    obj.delete()
    return JsonResponse({"ok": True})


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

    # 🔥 FIX: si el front manda fecha_cotizacion (viejo nombre), lo mapeamos a 'fecha'
    fecha_str = (request.GET.get("fecha") or request.GET.get("fecha_cotizacion") or "").strip()
    fecha = _parse_date(fecha_str)

    qs = Cotizacion.objects.select_related("cliente").all()

    # filtro por estado
    estados_validos = dict(CotizacionEstado.choices)
    if estado in estados_validos:
        qs = qs.filter(estado=estado)

    # filtro por fecha (campo real es 'fecha')
    if fecha:
        qs = qs.filter(fecha=fecha)

    # búsqueda general
    if q:
        qs = qs.filter(
            Q(codigo__icontains=q)
            | Q(cliente__razon_social__icontains=q)
            | Q(cliente__rut__icontains=q)
            | Q(terminos__icontains=q)
        )

    # orden razonable (si existe created_at, úsalo; si no, por id)
    if hasattr(Cotizacion, "created_at"):
        qs = qs.order_by("-created_at", "-id")
    else:
        qs = qs.order_by("-id")

    return render(
        request,
        "centro_comercio/cotizaciones/_tabla.html",
        {
            "cotizaciones": qs,
            "q": q,
            "estado": estado,
            "estados": CotizacionEstado.choices,
            "fecha": fecha_str,  # lo devolvemos para mantener input
        },
    )


@login_required
def cotizacion_detalle(request, pk: int):
    obj = get_object_or_404(
        Cotizacion.objects.select_related("cliente").prefetch_related("items"),
        pk=pk,
    )
    return render(request, "centro_comercio/cotizaciones/_detalle.html", {"c": obj})


@login_required
@transaction.atomic
def cotizacion_form(request, pk: int = None):
    obj = get_object_or_404(Cotizacion, pk=pk) if pk else None

    if request.method == "POST":
        form = CotizacionForm(request.POST, instance=obj)
        formset = CotizacionItemFormSet(request.POST, instance=obj)

        if form.is_valid() and formset.is_valid():
            cot = form.save(commit=False)

            # si no trae código, generamos
            if not getattr(cot, "codigo", None):
                cot.codigo = Cotizacion.siguiente_codigo()

            cot.save()

            formset.instance = cot
            formset.save()

            # ✅ AJAX -> JSON
            if _is_ajax(request):
                return JsonResponse({"ok": True, "id": cot.id})

            # ✅ normal -> panel
            return redirect(f"{reverse('centro_comercio:cotizaciones_panel')}?open={cot.id}")

        if _is_ajax(request):
            return JsonResponse(
                {
                    "ok": False,
                    "errors": form.errors,
                    "formset_errors": formset.errors,
                    "non_form_errors": formset.non_form_errors(),
                },
                status=400,
            )

        return render(
            request,
            "centro_comercio/cotizaciones/_form.html",
            {"form": form, "formset": formset, "obj": obj},
            status=400,
        )

    # GET
    if obj is None:
        initial = {"codigo": Cotizacion.siguiente_codigo()}
        form = CotizacionForm(initial=initial)
        formset = CotizacionItemFormSet()
    else:
        form = CotizacionForm(instance=obj)
        formset = CotizacionItemFormSet(instance=obj)

    return render(
        request,
        "centro_comercio/cotizaciones/_form.html",
        {"form": form, "formset": formset, "obj": obj},
    )


@login_required
@require_POST
def cotizacion_eliminar(request, pk: int):
    obj = get_object_or_404(Cotizacion, pk=pk)
    obj.delete()
    return JsonResponse({"ok": True})
