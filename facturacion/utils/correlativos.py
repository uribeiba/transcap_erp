from facturacion.models import Correlativo
from django.utils import timezone

def reiniciar_correlativos_si_nuevo_anio():
    año_actual = timezone.now().year
    for corr in Correlativo.objects.all():
        if corr.anio != año_actual:
            corr.ultimo_folio = 0
            corr.anio = año_actual
            corr.save()