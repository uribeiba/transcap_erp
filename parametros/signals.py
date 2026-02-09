# parametros/signals.py
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Perfil, Empresa, Sucursal, RolUsuario

User = get_user_model()


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea SOLO el Perfil básico al crear un usuario.
    No crea Empresa/Sucursal aquí (eso se hace bajo demanda en vistas).
    """
    if created:
        Perfil.objects.get_or_create(user=instance)


def asegurar_empresa_para_usuario(user):
    """
    Garantiza que el usuario tenga:
    - Perfil
    - Empresa
    - Sucursal
    Se llama desde vistas (no desde signals).

    Protegido con transaction para evitar duplicados por concurrencia.
    """
    with transaction.atomic():
        perfil, _ = Perfil.objects.select_for_update().get_or_create(user=user)

        # Si ya tiene empresa, aseguramos sucursal mínima y listo
        if perfil.empresa_id:
            if not perfil.sucursal_id:
                suc = Sucursal.objects.filter(empresa=perfil.empresa).order_by("nombre").first()
                if not suc:
                    suc = Sucursal.objects.create(empresa=perfil.empresa, nombre="matriz")
                perfil.sucursal = suc
                perfil.save(update_fields=["sucursal"])
            return perfil

        nombre = (user.get_full_name() or user.get_username() or "Usuario").strip()

        empresa = Empresa.objects.create(
            razon_social=f"Empresa de {nombre}",
            rut="",
            direccion=""
        )

        # Siempre "matriz" en minúscula para consistencia en reglas/validaciones
    sucursal = Sucursal.objects.create(
    empresa=empresa,
    nombre="Matriz"  # Mantener consistencia con mayúscula inicial
)

    perfil.empresa = empresa
    perfil.sucursal = sucursal
    perfil.rol = RolUsuario.ADMIN if (user.is_superuser or user.is_staff) else RolUsuario.USER
    perfil.save(update_fields=["empresa", "sucursal", "rol"])

    return perfil
