from django.db import models
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import BitacoraForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from taller.models import CoordinacionViaje

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from centro_comercio.models import Cliente  # <-- este es el bueno (rut, razon_social, etc.)
from django.utils import timezone



@login_required
def panel(request):
    return render(request, "bitacora/panel.html")


# views.py - MODIFICAR LA FUNCIÓN crear
@login_required
def crear(request):
    if request.method == "POST":
        form = BitacoraForm(request.POST, user=request.user)  # Pasar usuario aquí
        if form.is_valid():
            obj = form.save(commit=False)
            obj.creado_por = request.user
            
            # Si el coordinador está vacío, usar el usuario actual
            if not obj.coordinador or obj.coordinador.strip() == '':
                obj.coordinador = request.user.get_full_name()
                
            obj.save()
            messages.success(request, "✅ Agenda creada correctamente.")
            return redirect("bitacora:panel")
    else:
        # Prellenar con datos del usuario
        initial_data = {
            'fecha': timezone.localdate(),
            'coordinador': request.user.get_full_name()  # Asegurar coordinador
        }
        form = BitacoraForm(initial=initial_data, user=request.user)  # Pasar usuario aquí

    return render(request, "bitacora/form.html", {"form": form})



def api_coordinacion_detalle(request, id):
    coord = get_object_or_404(CoordinacionViaje, pk=id)

    data = {
        "fecha_carga": coord.fecha_carga,
        "fecha_descarga": coord.fecha_descarga,
        "origen": coord.origen or "",
        "intermedio": "",  # 🔹 por ahora vacío
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
            models.Q(razon_social__icontains=q) |
            models.Q(rut__icontains=q)
        )

    qs = qs.order_by("razon_social")[:20]

    data = [
        {
            "id": c.id,
            "text": f"{c.razon_social} ({c.rut})",
            "razon_social": c.razon_social,
            "rut": c.rut,
            "giro": c.giro,
            "direccion": c.direccion,
            "localidad": c.localidad,
            "telefono": c.telefono,
            "email": c.email,
        }
        for c in qs
    ]
    return JsonResponse({"results": data})
