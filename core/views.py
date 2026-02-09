from django.utils import timezone
from taller.models import DocumentoVehiculo, DocumentoConductor
from django.shortcuts import render  # <-- necesario para render()



def dashboard(request):
    # Métricas demo (luego las conectamos a la BD)
    context = {
        "estado_resultado": 425_980_630,
        "cuentas_por_cobrar": -45_673_728,
        "cuentas_por_pagar": -16_666_813,
        "flujo_caja": 581_374_116,
    }

    # ---- Widgets: Documentos (vehículos / conductores) ----
    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)

    docs_v_vencidos = DocumentoVehiculo.objects.filter(fecha_vencimiento__lt=hoy).count()
    docs_v_porvencer = DocumentoVehiculo.objects.filter(
        fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite
    ).count()

    docs_c_vencidos = DocumentoConductor.objects.filter(fecha_vencimiento__lt=hoy).count()
    docs_c_porvencer = DocumentoConductor.objects.filter(
        fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite
    ).count()

    context.update({
        "docs_widget": {
            "vehiculos": {"vencidos": docs_v_vencidos, "por_vencer": docs_v_porvencer},
            "conductores": {"vencidos": docs_c_vencidos, "por_vencer": docs_c_porvencer},
            "hoy": hoy,
            "limite": limite,
        }
    })

    return render(request, "core/dashboard.html", context)
