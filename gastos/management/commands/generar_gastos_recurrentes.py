from django.core.management.base import BaseCommand
from django.utils import timezone
from gastos.models import GastoRecurrente, Gasto
from datetime import date, timedelta
from calendar import monthrange

class Command(BaseCommand):
    help = 'Genera gastos recurrentes para el mes actual si no existen'

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        primer_dia_mes = hoy.replace(day=1)
        for recurrente in GastoRecurrente.objects.filter(activo=True):
            # Verificar si ya se generó este mes
            existe = Gasto.objects.filter(
                descripcion__icontains=recurrente.descripcion,
                fecha__year=hoy.year,
                fecha__month=hoy.month,
                categoria=recurrente.categoria,
                monto_neto=recurrente.monto_neto
            ).exists()
            if not existe:
                # Calcular día de pago
                if recurrente.dia_pago == -1:
                    ultimo_dia = monthrange(hoy.year, hoy.month)[1]
                    dia_pago = ultimo_dia
                else:
                    dia_pago = recurrente.dia_pago
                try:
                    fecha_pago = date(hoy.year, hoy.month, dia_pago)
                except ValueError:
                    # Si el día no existe (ej. 31 en febrero), usar último día
                    ultimo_dia = monthrange(hoy.year, hoy.month)[1]
                    fecha_pago = date(hoy.year, hoy.month, ultimo_dia)

                Gasto.objects.create(
                    fecha=primer_dia_mes,
                    categoria=recurrente.categoria,
                    proveedor=recurrente.proveedor,
                    descripcion=recurrente.descripcion,
                    monto_neto=recurrente.monto_neto,
                    iva=recurrente.iva,
                    fecha_vencimiento=fecha_pago,
                    pagado=False,
                    observaciones=f"Generado automáticamente desde servicio recurrente #{recurrente.id}"
                )
                self.stdout.write(self.style.SUCCESS(f'Generado gasto: {recurrente.descripcion}'))
        self.stdout.write(self.style.SUCCESS('Proceso finalizado'))