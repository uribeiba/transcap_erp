# suscripciones/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import Plan
from .forms import PlanForm


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


@login_required
def planes_list(request):
    planes = Plan.objects.all().order_by("orden", "max_usuarios", "nombre")
    return render(request, "suscripciones/planes_list.html", {"planes": planes})


@login_required
@require_http_methods(["GET", "POST"])
def plan_crear(request):
    form = PlanForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            plan = form.save()
            if _is_ajax(request):
                return JsonResponse({"ok": True, "message": "Plan creado"})
            messages.success(request, "Plan creado correctamente")
            return redirect("suscripciones:planes_list")
        else:
            if _is_ajax(request):
                return render(request, "suscripciones/plan_form_modal.html", {"form": form, "titulo": "Nuevo Plan"})
    # GET
    if _is_ajax(request):
        return render(request, "suscripciones/plan_form_modal.html", {"form": form, "titulo": "Nuevo Plan"})
    return render(request, "suscripciones/plan_form_page.html", {"form": form, "titulo": "Nuevo Plan"})


@login_required
@require_http_methods(["GET", "POST"])
def plan_editar(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    form = PlanForm(request.POST or None, instance=plan)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            if _is_ajax(request):
                return JsonResponse({"ok": True, "message": "Plan actualizado"})
            messages.success(request, "Plan actualizado correctamente")
            return redirect("suscripciones:planes_list")
        else:
            if _is_ajax(request):
                return render(
                    request,
                    "suscripciones/plan_form_modal.html",
                    {"form": form, "titulo": "Editar Plan"},
                )

    # GET
    if _is_ajax(request):
        return render(
            request,
            "suscripciones/plan_form_modal.html",
            {"form": form, "titulo": "Editar Plan"},
        )
    return render(request, "suscripciones/plan_form_page.html", {"form": form, "titulo": "Editar Plan"})


@login_required
@require_http_methods(["POST"])
def plan_eliminar(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    plan.delete()
    if _is_ajax(request):
        return JsonResponse({"ok": True, "message": "Plan eliminado"})
    messages.success(request, "Plan eliminado correctamente")
    return redirect("suscripciones:planes_list")
