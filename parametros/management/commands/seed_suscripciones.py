from django.core.management.base import BaseCommand
from parametros.models import Empresa
from suscripciones.services import asegurar_suscripcion_empresa


class Command(BaseCommand):
    help = "Crea suscripciones para empresas existentes que no tengan."

    def handle(self, *args, **options):
        count = 0
        for emp in Empresa.objects.all():
            sus = asegurar_suscripcion_empresa(emp)
            count += 1
            self.stdout.write(self.style.SUCCESS(f"OK: {emp} -> {sus.plan.nombre}"))
        self.stdout.write(self.style.SUCCESS(f"Listo. Revisadas {count} empresas."))
