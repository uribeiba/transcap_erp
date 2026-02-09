from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import asegurar_suscripcion_empresa


# OJO: esto se evalúa cuando se importa signals.py desde apps.ready(),
# por lo que el registry ya está listo y apps.get_model funciona.
Empresa = apps.get_model("parametros", "Empresa")


@receiver(post_save, sender=Empresa)
def crear_suscripcion_por_defecto(sender, instance, created, **kwargs):
    """
    MVP: cada vez que se crea una Empresa, se asegura su suscripción base.
    """
    if created:
        asegurar_suscripcion_empresa(instance)
