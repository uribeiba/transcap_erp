from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PlanForm
from .models import Plan


@login_required
def planes_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Plan.objects.all().order_by("orden", "max_usuarios", "nombre")
    if q:
        qs = qs.filter(nombre__icontains=q)
    return render(request, "suscripciones/planes_list.html", {"planes": qs, "q": q})


@login_required
def plan_crear(request):
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan creado correctamente.")
            return redirect("suscripciones:planes_list")
    else:
        form = PlanForm()
    return render(request, "suscripciones/plan_form.html", {"form": form, "modo": "crear"})


@login_required
def plan_editar(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan actualizado correctamente.")
            return redirect("suscripciones:planes_list")
    else:
        form = PlanForm(instance=plan)
    return render(request, "suscripciones/plan_form.html", {"form": form, "plan": plan, "modo": "editar"})


@login_required
def plan_toggle_activo(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    plan.activo = not plan.activo
    plan.save(update_fields=["activo"])
    messages.success(request, f"Plan {'activado' if plan.activo else 'desactivado'}: {plan.nombre}")
    return redirect("suscripciones:planes_list")
