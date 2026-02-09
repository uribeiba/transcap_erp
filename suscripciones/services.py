# suscripciones/services.py
from django.db import transaction
from django.utils import timezone

from .models import Plan, Suscripcion
from django.db import transaction


def obtener_plan_basico():
    """
    Devuelve el plan activo más básico (por max_usuarios).
    Si no existe ninguno, lo crea.
    """
    plan = (
        Plan.objects.filter(activo=True)
        .order_by("max_usuarios", "id")
        .first()
    )
    if plan:
        return plan

    # Crear uno mínimo (sin inventar campos raros)
    return Plan.objects.create(
        nombre="Básico",
        max_usuarios=1,
        max_empresas=1,
        activo=True,
        precio_mensual=0,
        precio_anual=0,
    )


@transaction.atomic
def asegurar_suscripcion_empresa(empresa):
    """
    Garantiza que una Empresa tenga una Suscripción.
    - Si existe, la devuelve (y repara limite_usuarios si viene vacío).
    - Si no existe, crea una ACTIVA con el plan básico.
    - Usa select_for_update para evitar duplicados por concurrencia.
    """
    # Bloqueamos la fila de empresa indirectamente mediante la búsqueda de Suscripcion
    sus = (
        Suscripcion.objects.select_for_update()
        .filter(empresa=empresa)
        .select_related("plan")
        .first()
    )

    if sus:
        # Repara limite si venía mal
        if not sus.limite_usuarios:
            sus.limite_usuarios = sus.plan.max_usuarios
            sus.save(update_fields=["limite_usuarios"])
        return sus

    plan_basico = obtener_plan_basico()

    sus = Suscripcion.objects.create(
        empresa=empresa,
        plan=plan_basico,
        estado="ACTIVA",
        inicio=timezone.now().date(),
        limite_usuarios=plan_basico.max_usuarios,
    )
    return sus


def puede_crear_usuario(empresa) -> tuple[bool, int, int, str]:
    """
    Retorna (ok, usados, max, mensaje)
    """
    sus = asegurar_suscripcion_empresa(empresa)
    max_u = sus.limite_usuarios or sus.plan.max_usuarios

    # OJO: esto depende de tu modelo Perfil relacionado a Empresa
    usados = empresa.perfiles.select_related("user").count()

    if max_u and usados >= max_u:
        return (False, usados, max_u, "Límite de usuarios alcanzado según el plan.")
    return (True, usados, max_u, "")



@transaction.atomic
def cambiar_plan_empresa(empresa, nuevo_plan):
    """
    Cambia el plan de una empresa.
    Reglas:
    - Si la empresa tiene más usuarios que el límite del nuevo plan: NO deja bajar.
    - Si ok: actualiza plan + congela limite_usuarios según nuevo plan.
    """
    sus = asegurar_suscripcion_empresa(empresa)

    # usuarios usados (según tu Perfil->empresa)
    usados = empresa.perfiles.select_related("user").count()
    limite = int(nuevo_plan.max_usuarios or 0)

    if limite and usados > limite:
        return {
            "ok": False,
            "error": f"No puedes bajar a este plan. Tienes {usados} usuarios y el plan permite {limite}.",
            "usados": usados,
            "limite": limite,
        }

    sus.plan = nuevo_plan
    sus.limite_usuarios = nuevo_plan.max_usuarios
    sus.save(update_fields=["plan", "limite_usuarios"])

    return {"ok": True, "usados": usados, "limite": limite}





def get_plan_basico():
    """
    Devuelve el plan activo más básico.
    Si no existe ninguno, crea uno por defecto.
    """
    plan = (
        Plan.objects.filter(activo=True)
        .order_by("orden", "max_usuarios", "id")
        .first()
    )

    if plan:
        return plan

    # Fallback seguro (no revienta el sistema si te olvidaste de crear planes)
    return Plan.objects.create(
        nombre="Básico",
        max_usuarios=1,
        max_empresas=1,
        precio_mensual=0,
        precio_anual=0,
        descripcion="Plan básico autogenerado",
        orden=1,
        activo=True,
    )


def asegurar_suscripcion_empresa(empresa):
    """
    Garantiza que una Empresa tenga una Suscripción en la app suscripciones.
    - Si existe: sincroniza limite_usuarios si está vacío.
    - Si no existe: crea ACTIVA con plan básico.
    """
    try:
        sus = empresa.suscripcion  # related_name oficial en Suscripcion (suscripciones)
        if not sus.limite_usuarios:
            sus.limite_usuarios = sus.plan.max_usuarios
            sus.save(update_fields=["limite_usuarios"])
        return sus
    except Suscripcion.DoesNotExist:
        pass

    plan_basico = get_plan_basico()

    with transaction.atomic():
        sus = Suscripcion.objects.create(
            empresa=empresa,
            plan=plan_basico,
            estado="ACTIVA",
            inicio=timezone.now().date(),
            limite_usuarios=plan_basico.max_usuarios,
        )
    return sus


def puede_crear_usuario(empresa) -> bool:
    """
    Regla simple: usuarios actuales < limite del plan
    (Ajusta a tu forma real de contar usuarios por empresa).
    """
    sus = asegurar_suscripcion_empresa(empresa)
    # asumiendo que tus usuarios de empresa vienen por Perfil. Si tu relación es otra, me dices y lo ajusto.
    usados = empresa.perfiles.select_related("user").filter(user__is_active=True).count()
    return usados < (sus.limite_usuarios or sus.plan.max_usuarios or 0)


def resumen_limite_usuarios(empresa):
    """
    Devuelve (usados, max, mensaje, puede_crear)
    útil para tu panel.
    """
    sus = asegurar_suscripcion_empresa(empresa)
    max_u = sus.limite_usuarios or sus.plan.max_usuarios or 0
    usados = empresa.perfiles.select_related("user").filter(user__is_active=True).count()
    puede = usados < max_u if max_u else True
    msg = ""
    if max_u and not puede:
        msg = "Límite de usuarios alcanzado según el plan."
    return usados, max_u, msg, puede

