# parametros/views.py
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from suscripciones.services import asegurar_suscripcion_empresa, cambiar_plan_empresa

from .forms import (
    EmpresaForm,
    LogoEmpresaForm,
    SucursalForm,
    UsuarioCreateForm,
    UsuarioEditForm,
    UsuarioPasswordForm,
)
from .models import Empresa, Perfil, RolUsuario, Sucursal
from .signals import asegurar_empresa_para_usuario
from django.views.decorators.http import require_http_methods

from suscripciones.models import Plan
from suscripciones.forms import PlanForm
from suscripciones.forms import CambiarPlanForm

User = get_user_model()


# =========================
# Helpers
# =========================
def _is_ajax(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _json_ok(**extra):
    data = {"ok": True}
    data.update(extra)
    return JsonResponse(data)


def _json_err(msg: str, status: int = 400, **extra):
    data = {"ok": False, "error": msg}
    data.update(extra)
    return JsonResponse(data, status=status)


def _perfil(request):
    if not request.user.is_authenticated:
        raise Http404("No autenticado")

    p = getattr(request.user, "perfil", None)
    if not p or not getattr(p, "empresa_id", None):
        p = asegurar_empresa_para_usuario(request.user)

    # asegurar sucursal (matriz por defecto)
    if not getattr(p, "sucursal_id", None):
        suc = Sucursal.objects.filter(empresa=p.empresa).order_by("nombre").first()
        if not suc:
            suc = Sucursal.objects.create(empresa=p.empresa, nombre="Matriz")
        p.sucursal = suc
        p.save(update_fields=["sucursal"])

    return p


def _empresa(request):
    """
    Tenant activo:
    - normal: perfil.empresa
    - SUPERADMIN: puede "entrar" a otra empresa con session['empresa_activa_id']
    Además asegura suscripción (MVP).
    """
    perfil = _perfil(request)
    empresa = perfil.empresa

    # 👇 Solo superuser puede "cambiar tenant" por sesión
    empresa_activa_id = request.session.get("empresa_activa_id")
    if request.user.is_superuser and empresa_activa_id:
        try:
            empresa = Empresa.objects.get(pk=empresa_activa_id)
        except Empresa.DoesNotExist:
            request.session.pop("empresa_activa_id", None)
            empresa = perfil.empresa

    # ✅ Asegura suscripción
    asegurar_suscripcion_empresa(empresa)
    return empresa



def _is_admin(request) -> bool:
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.rol == RolUsuario.ADMIN
    except Exception:
        return False


def empresa_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        _perfil(request)
        if not _is_admin(request):
            msg = "Acceso denegado: requiere rol Administrador."
            if _is_ajax(request):
                return _json_err(msg, status=403)
            messages.error(request, msg)
            return redirect("parametros:panel")
        return view_func(request, *args, **kwargs)

    return _wrapped


# =========================
# Suscripción / Cupos (SaaS)
# =========================
def _get_max_usuarios_from_suscripcion(suscripcion):
    """
    Lee el cupo desde nombres posibles (por si cambiaste campos):
    - suscripcion.max_usuarios / limite_usuarios / usuarios_max
    - plan.max_usuarios / limite_usuarios / usuarios_max
    """
    if not suscripcion:
        return None

    # en la suscripción
    for attr in ("max_usuarios", "limite_usuarios", "usuarios_max"):
        if hasattr(suscripcion, attr):
            val = getattr(suscripcion, attr)
            if val not in ("", None):
                return val

    # en el plan asociado
    plan = getattr(suscripcion, "plan", None)
    if plan:
        for attr in ("max_usuarios", "limite_usuarios", "usuarios_max"):
            if hasattr(plan, attr):
                val = getattr(plan, attr)
                if val not in ("", None):
                    return val

    return None


def _usuarios_count_empresa(empresa):
    """
    Cuenta usuarios activos de la empresa (tenant).
    Si quieres contar también inactivos, quita is_active=True.
    """
    return User.objects.filter(perfil__empresa=empresa, is_active=True).count()


def _check_cupo_usuarios(request, empresa):
    """
    ✅ 9) BLOQUEO por plan:
    - Obtiene suscripción (asegurada en _empresa)
    - Lee max_usuarios
    - Compara con usuarios activos
    """
    try:
        sus = asegurar_suscripcion_empresa(empresa)
    except Exception:
        sus = None

    max_usuarios = _get_max_usuarios_from_suscripcion(sus)

    # Si no hay límite definido -> sin bloqueo
    if max_usuarios in (None, "", 0):
        return True, None, sus, None, _usuarios_count_empresa(empresa)

    try:
        max_usuarios_int = int(max_usuarios)
    except Exception:
        # si está mal seteado el campo, no bloqueamos
        return True, None, sus, max_usuarios, _usuarios_count_empresa(empresa)

    usados = _usuarios_count_empresa(empresa)
    if usados >= max_usuarios_int:
        msg = f"⛔ Límite de usuarios alcanzado ({usados}/{max_usuarios_int}). Debes subir de plan para crear más usuarios."
        return False, msg, sus, max_usuarios_int, usados

    return True, None, sus, max_usuarios_int, usados


# =========================
# Panel
# =========================
@login_required
def panel(request):
    perfil = _perfil(request)
    empresa = _empresa(request)  # 👈 usa tenant activo (con switch)

    matriz_exists = Sucursal.objects.filter(empresa=empresa, nombre__iexact="matriz").exists()
    if not matriz_exists:
        Sucursal.objects.create(empresa=empresa, nombre="Matriz")

    sucursales = Sucursal.objects.filter(empresa=empresa).order_by("nombre")
    usuarios = (
        User.objects.filter(perfil__empresa=empresa)
        .select_related("perfil", "perfil__sucursal")
        .order_by("first_name", "last_name", "username")
    )

    # ✅ SaaS: datos de suscripción para el panel
    suscripcion = getattr(empresa, "suscripcion", None)  # si asegurar_suscripcion_empresa ya corrió, debería existir
    plan_nombre = None
    estado_suscripcion = None
    vigente_hasta = None
    max_usuarios = 0

    if suscripcion:
        plan_nombre = getattr(getattr(suscripcion, "plan", None), "nombre", None)
        estado_suscripcion = getattr(suscripcion, "estado", None)
        vigente_hasta = getattr(suscripcion, "fecha_fin", None)
        # límite de usuarios: preferimos suscripcion.limite_usuarios, sino plan.max_usuarios
        max_usuarios = int(getattr(suscripcion, "limite_usuarios", 0) or 0)
        if not max_usuarios and getattr(suscripcion, "plan", None):
            max_usuarios = int(getattr(suscripcion.plan, "max_usuarios", 0) or 0)

    usuarios_count = usuarios.count()
    puede_crear_usuario = True
    mensaje_limite = ""

    # ✅ regla: si está SUSPENDIDA/VENCIDA => bloquear creación
    if suscripcion and estado_suscripcion in ("SUSPENDIDA", "VENCIDA"):
        puede_crear_usuario = False
        mensaje_limite = "Tu suscripción no está activa. No puedes crear usuarios."

    # ✅ regla: límite por plan
    if max_usuarios and usuarios_count >= max_usuarios:
        puede_crear_usuario = False
        if not mensaje_limite:
            mensaje_limite = "Límite de usuarios alcanzado según el plan."

    return render(
        request,
        "parametros/panel.html",
        {
            "empresa": empresa,
            "sucursales": sucursales,
            "usuarios": usuarios,
            "perfil": perfil,

            # ✅ variables para tu panel SaaS
            "suscripcion": suscripcion,
            "plan_nombre": plan_nombre,
            "estado_suscripcion": estado_suscripcion,
            "vigente_hasta": vigente_hasta,
            "max_usuarios": max_usuarios,
            "puede_crear_usuario": puede_crear_usuario,
            "mensaje_limite": mensaje_limite,
        },
    )


# =========================
# Empresa (tenant actual)
# =========================
@login_required
@empresa_admin_required
def empresa_update(request):
    empresa = _empresa(request)

    if request.method == "POST":
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()

            if _is_ajax(request):
                return _json_ok(message="Empresa actualizada.", redirect=reverse("parametros:panel"))

            messages.success(request, "✅ Empresa actualizada.")
            return redirect("parametros:panel")
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, "parametros/empresa_form.html", {"form": form, "empresa": empresa})


@login_required
@empresa_admin_required
def empresa_logo_update(request):
    empresa = _empresa(request)

    if request.method == "POST":
        form = LogoEmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()

            if _is_ajax(request):
                return _json_ok(message="Logo actualizado.", redirect=reverse("parametros:panel"))

            messages.success(request, "✅ Logo actualizado.")
            return redirect("parametros:panel")
    else:
        form = LogoEmpresaForm(instance=empresa)

    return render(request, "parametros/logo_form.html", {"form": form, "empresa": empresa})


# =========================
# Sucursales
# =========================
@login_required
@empresa_admin_required
def sucursal_create(request):
    empresa = _empresa(request)

    if request.method == "POST":
        try:
            form = SucursalForm(request.POST, empresa=empresa)
        except TypeError:
            form = SucursalForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.nombre = (obj.nombre or "").strip()

            if Sucursal.objects.filter(empresa=empresa, nombre__iexact=obj.nombre).exists():
                msg = "⛔ Ya existe una sucursal con ese nombre."
                if _is_ajax(request):
                    return _json_err(msg)
                messages.error(request, msg)
                return redirect("parametros:panel")

            obj.save()
            if _is_ajax(request):
                return _json_ok(message="Sucursal creada.", redirect=reverse("parametros:panel"))
            messages.success(request, "✅ Sucursal creada.")
            return redirect("parametros:panel")
    else:
        try:
            form = SucursalForm(empresa=empresa)
        except TypeError:
            form = SucursalForm()

    return render(request, "parametros/modals/sucursal_form.html", {"form": form, "modo": "crear"})


@login_required
@empresa_admin_required
def sucursal_update(request, pk):
    empresa = _empresa(request)
    sucursal = get_object_or_404(Sucursal, pk=pk, empresa=empresa)

    if request.method == "POST":
        try:
            form = SucursalForm(request.POST, instance=sucursal, empresa=empresa)
        except TypeError:
            form = SucursalForm(request.POST, instance=sucursal)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.nombre = (obj.nombre or "").strip()

            if (
                Sucursal.objects.filter(empresa=empresa, nombre__iexact=obj.nombre)
                .exclude(pk=sucursal.pk)
                .exists()
            ):
                msg = "⛔ Ya existe otra sucursal con ese nombre."
                if _is_ajax(request):
                    return _json_err(msg)
                messages.error(request, msg)
                return redirect("parametros:panel")

            obj.save()
            if _is_ajax(request):
                return _json_ok(message="Sucursal actualizada.", redirect=reverse("parametros:panel"))
            messages.success(request, "✅ Sucursal actualizada.")
            return redirect("parametros:panel")
    else:
        try:
            form = SucursalForm(instance=sucursal, empresa=empresa)
        except TypeError:
            form = SucursalForm(instance=sucursal)

    return render(
        request,
        "parametros/modals/sucursal_form.html",
        {"form": form, "modo": "editar", "sucursal": sucursal},
    )


@login_required
@empresa_admin_required
def sucursal_delete(request, pk):
    empresa = _empresa(request)
    sucursal = get_object_or_404(Sucursal, pk=pk, empresa=empresa)

    nombre_norm = (sucursal.nombre or "").strip().lower()

    # ineliminable
    if nombre_norm == "matriz":
        msg = "⛔ No puedes eliminar la sucursal 'Matriz'."

        if request.method == "POST":
            if _is_ajax(request):
                return _json_err(msg)
            messages.error(request, msg)
            return redirect("parametros:panel")

        return render(
            request,
            "parametros/confirmar_eliminar.html",
            {
                "titulo": "Acción no permitida",
                "mensaje": msg,
                "volver_href": reverse("parametros:panel"),
                "is_modal": _is_ajax(request),
                "allow_delete": False,
            },
        )

    # no eliminar si hay usuarios
    if Perfil.objects.filter(empresa=empresa, sucursal=sucursal).exists():
        msg = "⛔ No puedes eliminar: hay usuarios asignados a esta sucursal."

        if request.method != "POST":
            return render(
                request,
                "parametros/confirmar_eliminar.html",
                {
                    "titulo": "Acción no permitida",
                    "mensaje": msg,
                    "volver_href": reverse("parametros:panel"),
                    "is_modal": _is_ajax(request),
                    "allow_delete": False,
                },
            )

        if _is_ajax(request):
            return _json_err(msg)
        messages.error(request, msg)
        return redirect("parametros:panel")

    if request.method == "POST":
        sucursal.delete()
        if _is_ajax(request):
            return _json_ok(message="Sucursal eliminada.", redirect=reverse("parametros:panel"))
        messages.success(request, "✅ Sucursal eliminada.")
        return redirect("parametros:panel")

    return render(
        request,
        "parametros/confirmar_eliminar.html",
        {
            "titulo": "Eliminar Sucursal",
            "mensaje": f"¿Eliminar la sucursal '{sucursal.nombre}'?",
            "volver_href": reverse("parametros:panel"),
            "is_modal": _is_ajax(request),
            "allow_delete": True,
        },
    )


# =========================
# Usuarios
# =========================
@login_required
@empresa_admin_required
def usuario_create(request):
    empresa = _empresa(request)

    # ✅ 9) bloquear por plan (también en GET del modal)
    cupo_ok, cupo_msg, suscripcion, max_usuarios, usuarios_usados = _check_cupo_usuarios(request, empresa)
    if not cupo_ok:
        if _is_ajax(request):
            return _json_err(cupo_msg, status=403)
        messages.error(request, cupo_msg)
        return redirect("parametros:panel")

    if request.method == "POST":
        # 🔒 Re-check por si otro admin creó un usuario entre medio
        cupo_ok2, cupo_msg2, _, _, _ = _check_cupo_usuarios(request, empresa)
        if not cupo_ok2:
            if _is_ajax(request):
                return _json_err(cupo_msg2, status=403)
            messages.error(request, cupo_msg2)
            return redirect("parametros:panel")

        form = UsuarioCreateForm(request.POST, empresa=empresa)
        if form.is_valid():
            email = (form.cleaned_data.get("email") or "").strip().lower()
            username = email or f"user{User.objects.count() + 1}"

            user = User.objects.create(
                username=username,
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                email=email,
                is_active=form.cleaned_data.get("is_active", True),
            )
            user.set_password(form.cleaned_data["password1"])
            user.save()

            perfil, _ = Perfil.objects.get_or_create(user=user)
            perfil.empresa = empresa
            perfil.sucursal = form.cleaned_data.get("sucursal")
            perfil.rol = form.cleaned_data.get("rol")
            perfil.save()

            if _is_ajax(request):
                return _json_ok(message="Usuario creado.", redirect=reverse("parametros:panel"))
            messages.success(request, "✅ Usuario creado.")
            return redirect("parametros:panel")
    else:
        form = UsuarioCreateForm(empresa=empresa)

    return render(request, "parametros/modals/usuario_form.html", {"form": form, "modo": "crear"})


@login_required
@empresa_admin_required
def usuario_update(request, pk):
    empresa = _empresa(request)
    user = get_object_or_404(User, pk=pk, perfil__empresa=empresa)
    perfil, _ = Perfil.objects.get_or_create(user=user)

    if request.method == "POST":
        form = UsuarioEditForm(request.POST, instance=user, empresa=empresa)
        pass_form = UsuarioPasswordForm(user, request.POST)

        cambiar_pass = request.POST.get("cambiar_password") == "SI"

        if form.is_valid() and (not cambiar_pass or pass_form.is_valid()):
            form.save()

            perfil.empresa = empresa
            perfil.sucursal = form.cleaned_data.get("sucursal")
            perfil.rol = form.cleaned_data.get("rol")
            perfil.save()

            if cambiar_pass:
                pass_form.save()

            if _is_ajax(request):
                return _json_ok(message="Usuario actualizado.", redirect=reverse("parametros:panel"))
            messages.success(request, "✅ Usuario actualizado.")
            return redirect("parametros:panel")
    else:
        form = UsuarioEditForm(
            instance=user,
            empresa=empresa,
            initial={"rol": perfil.rol, "sucursal": perfil.sucursal_id},
        )
        pass_form = UsuarioPasswordForm(user)

    return render(
        request,
        "parametros/modals/usuario_edit_form.html",
        {"form": form, "pass_form": pass_form, "user_obj": user},
    )


@login_required
@empresa_admin_required
@require_POST
def usuario_delete(request, pk):
    empresa = _empresa(request)
    usuario = get_object_or_404(User, pk=pk, perfil__empresa=empresa)

    if usuario.pk == request.user.pk:
        return _json_err("⛔ No puedes eliminar tu propio usuario.", status=400)

    if getattr(usuario, "is_superuser", False):
        return _json_err("⛔ No puedes eliminar un superusuario.", status=400)

    try:
        if usuario.perfil.empresa_id != empresa.id:
            return _json_err("⛔ No tienes permisos para eliminar usuarios de otra empresa.", status=403)
    except Exception:
        return _json_err("⛔ Usuario sin perfil asociado. No es seguro eliminarlo desde aquí.", status=400)

    with transaction.atomic():
        usuario.delete()

    return _json_ok(message="✅ Usuario eliminado.", redirect=reverse("parametros:panel"))


# =========================
# Administración de Empresas (solo ADMIN)
# =========================
@login_required
@empresa_admin_required
def empresas_panel(request):
    empresas = Empresa.objects.all().order_by("razon_social")

    # ✅ IMPORTANTE: siempre pasar esto al template (puede ser None)
    empresa_activa_id = request.session.get("empresa_activa_id")

    return render(
        request,
        "parametros/empresas_panel.html",
        {
            "empresas": empresas,
            "empresa_activa_id": empresa_activa_id,
        },
    )


@login_required
@empresa_admin_required
def empresa_create(request):
    if request.method == "POST":
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()

            # ✅ 6/8: asegura suscripción apenas se crea (MVP)
            try:
                asegurar_suscripcion_empresa(empresa)
            except Exception:
                pass

            if _is_ajax(request):
                return _json_ok(message="Empresa creada.", redirect=reverse("parametros:empresas_panel"))
            messages.success(request, "✅ Empresa creada.")
            return redirect("parametros:empresas_panel")
    else:
        form = EmpresaForm()

    return render(request, "parametros/empresa_form.html", {"form": form, "empresa": None})


@login_required
@empresa_admin_required
def empresa_admin_update(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == "POST":
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            if _is_ajax(request):
                return _json_ok(message="Empresa actualizada.", redirect=reverse("parametros:empresas_panel"))
            messages.success(request, "✅ Empresa actualizada.")
            return redirect("parametros:empresas_panel")
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, "parametros/empresa_form.html", {"form": form, "empresa": empresa})


@login_required
@empresa_admin_required
def empresa_admin_logo_update(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == "POST":
        form = LogoEmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            if _is_ajax(request):
                return _json_ok(message="Logo actualizado.", redirect=reverse("parametros:empresas_panel"))
            messages.success(request, "✅ Logo actualizado.")
            return redirect("parametros:empresas_panel")
    else:
        form = LogoEmpresaForm(instance=empresa)

    return render(request, "parametros/logo_form.html", {"form": form, "empresa": empresa})


@login_required
@empresa_admin_required
@require_POST
def empresa_switch(request, pk):
    """
    SUPERADMIN: setea empresa activa (tenant) en sesión.
    """
    if not request.user.is_superuser:
        return _json_err("⛔ Solo el superusuario puede cambiar de empresa.", status=403)

    empresa = get_object_or_404(Empresa, pk=pk)
    request.session["empresa_activa_id"] = empresa.pk

    # asegura suscripción al entrar
    asegurar_suscripcion_empresa(empresa)

    if _is_ajax(request):
        return _json_ok(message=f"✅ Entraste a: {empresa.razon_social}", redirect=reverse("parametros:panel"))

    messages.success(request, f"✅ Entraste a: {empresa.razon_social}")
    return redirect("parametros:panel")


@login_required
@empresa_admin_required
@require_POST
def empresa_switch_clear(request):
    """
    SUPERADMIN: vuelve a su empresa original (perfil.empresa).
    """
    if not request.user.is_superuser:
        return _json_err("⛔ Solo el superusuario puede salir de empresa.", status=403)

    request.session.pop("empresa_activa_id", None)

    if _is_ajax(request):
        return _json_ok(message="✅ Volviste a tu empresa.", redirect=reverse("parametros:panel"))

    messages.success(request, "✅ Volviste a tu empresa.")
    return redirect("parametros:panel")



@login_required
def empresa_entrar(request, pk):
    """
    Deja la empresa seleccionada como 'empresa activa' en la sesión
    (modo SaaS / multi-tenant).
    """
    empresa = get_object_or_404(Empresa, pk=pk)

    # Guardamos la empresa activa en sesión
    request.session["empresa_activa_id"] = empresa.id

    # Opcional: si quieres que se refleje inmediatamente
    request.session.modified = True

    messages.success(request, f"Empresa activa: {empresa.razon_social}")
    return redirect("parametros:panel")


# ✅ helper para detectar AJAX como tú lo estás usando
def is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@login_required
@empresa_admin_required
def planes_panel(request):
    planes = Plan.objects.all().order_by("orden", "max_usuarios", "nombre")
    return render(request, "parametros/planes_panel.html", {"planes": planes})


@login_required
@empresa_admin_required
@require_http_methods(["GET", "POST"])
def plan_create(request):
    form = PlanForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            if is_ajax(request):
                return JsonResponse({"ok": True, "message": "Plan creado"})
            return JsonResponse({"ok": True})
        else:
            if is_ajax(request):
                html = render(request, "parametros/planes/_plan_form.html", {"form": form, "accion": "Crear"}).content.decode("utf-8")
                return JsonResponse({"ok": False, "html": html}, status=400)

    # GET
    if is_ajax(request):
        return render(request, "parametros/planes/_plan_form.html", {"form": form, "accion": "Crear"})
    return render(request, "parametros/planes/plan_form_full.html", {"form": form, "accion": "Crear"})


@login_required
@empresa_admin_required
@require_http_methods(["GET", "POST"])
def plan_update(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    form = PlanForm(request.POST or None, instance=plan)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            if is_ajax(request):
                return JsonResponse({"ok": True, "message": "Plan actualizado"})
            return JsonResponse({"ok": True})
        else:
            if is_ajax(request):
                html = render(request, "parametros/planes/_plan_form.html", {"form": form, "accion": "Editar"}).content.decode("utf-8")
                return JsonResponse({"ok": False, "html": html}, status=400)

    if is_ajax(request):
        return render(request, "parametros/planes/_plan_form.html", {"form": form, "accion": "Editar"})
    return render(request, "parametros/planes/plan_form_full.html", {"form": form, "accion": "Editar"})


@login_required
@empresa_admin_required
@require_http_methods(["GET", "POST"])
def plan_delete(request, pk):
    plan = get_object_or_404(Plan, pk=pk)

    if request.method == "POST":
        plan.delete()
        if is_ajax(request):
            return JsonResponse({"ok": True, "message": "Plan eliminado"})
        return JsonResponse({"ok": True})

    if is_ajax(request):
        return render(request, "parametros/planes/_plan_delete_confirm.html", {"plan": plan})
    return render(request, "parametros/planes/plan_delete_full.html", {"plan": plan})


@login_required
# @empresa_admin_required
def empresa_cambiar_plan(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)

    # asegurar suscripción para mostrar plan actual sin romper
    sus = asegurar_suscripcion_empresa(empresa)

    form = CambiarPlanForm(request.POST or None, initial={"plan": sus.plan_id})

    if request.method == "POST":
        if form.is_valid():
            nuevo_plan = form.cleaned_data["plan"]
            result = cambiar_plan_empresa(empresa, nuevo_plan)
            if result["ok"]:
                return JsonResponse({"ok": True, "message": "Plan actualizado correctamente"})
            return JsonResponse({"ok": False, "error": result["error"]})

        return render(
            request,
            "parametros/_empresa_cambiar_plan_form.html",
            {"form": form, "empresa": empresa, "sus": sus},
        )

    return render(
        request,
        "parametros/_empresa_cambiar_plan_form.html",
        {"form": form, "empresa": empresa, "sus": sus},
    )
    
    
    



@login_required
# @empresa_admin_required
def planes_panel(request):
    planes = Plan.objects.all().order_by("orden", "max_usuarios", "nombre")
    return render(request, "parametros/planes_panel.html", {"planes": planes})


@login_required
# @empresa_admin_required
def plan_crear(request):
    form = PlanForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True, "message": "Plan creado"})
        return render(request, "parametros/_plan_form.html", {"form": form, "modo": "crear"})
    return render(request, "parametros/_plan_form.html", {"form": form, "modo": "crear"})


@login_required
# @empresa_admin_required
def plan_editar(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    form = PlanForm(request.POST or None, instance=plan)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True, "message": "Plan actualizado"})
        return render(request, "parametros/_plan_form.html", {"form": form, "modo": "editar", "plan": plan})
    return render(request, "parametros/_plan_form.html", {"form": form, "modo": "editar", "plan": plan})


@login_required
# @empresa_admin_required
def plan_eliminar(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)

    if request.method == "POST":
        # “soft safety”: si tiene suscripciones, no elimines (opcional)
        if plan.suscripciones.exists():
            return JsonResponse({"ok": False, "error": "Este plan está en uso. No se puede eliminar."})
        plan.delete()
        return JsonResponse({"ok": True, "message": "Plan eliminado"})

    return render(request, "parametros/_plan_confirm_delete.html", {"plan": plan})
