# ============================================
# Imports estándar de Python
# ============================================
from decimal import Decimal
from datetime import date as date_cls

# ============================================
# Imports de Django
# ============================================
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.db.models import (
    Q,
    Sum,
    Count,
    F,
    DecimalField,
    ExpressionWrapper,
)
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

# ============================================
# Librerías externas
# ============================================
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from inventario.models import User
from roles.models import UsuarioRol,Rol

from django.contrib.auth.models import User


# ============================================
# Imports de la app local (taller)
# ============================================
from .models import (
    Taller,
    Mantenimiento,
    MultaConductor,
    DocumentoVehiculo,
    DocumentoConductor,
    Vehiculo,
    Conductor,
    RutaViaje,
    CoordinacionViaje,
    RepuestoMantenimiento,
)

from .forms import (
    VehiculoForm,
    ConductorForm,
    DocumentoVehiculoForm,
    DocumentoConductorForm,
    MantenimientoForm,
    RutaViajeForm,
    CoordinacionViajeForm,
    RepuestoMantenimientoForm,
)

from datetime import timedelta


# ============================================
# WIDGETS PARA FORMULARIOS
# ============================================

class DateInput(forms.DateInput):
    input_type = "date"


# ============================================
# VISTAS PARA VEHÍCULOS
# ============================================

def flota_lista(request):
    """Lista todos los vehículos registrados"""
    vehiculos = Vehiculo.objects.all()
    return render(request, "taller/flota_lista.html", {"vehiculos": vehiculos})


def vehiculo_crear(request):
    """Crea un nuevo vehículo"""
    if request.method == "POST":
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo creado correctamente.")
            return redirect("taller_flota")
    else:
        form = VehiculoForm()

    return render(
        request,
        "taller/vehiculo_form.html",
        {"form": form, "modo": "Crear"},
    )


def vehiculo_editar(request, pk):
    """Edita un vehículo existente"""
    vehiculo = get_object_or_404(Vehiculo, pk=pk)

    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado correctamente.")
            return redirect("taller_flota")
    else:
        form = VehiculoForm(instance=vehiculo)

    return render(
        request,
        "taller/vehiculo_form.html",
        {"form": form, "modo": "Editar", "vehiculo": vehiculo},
    )


# ============================================
# VISTAS PARA CONDUCTORES
# ============================================

def conductores_lista(request):
    """Lista todos los conductores activos"""
    conductores = Conductor.objects.filter(activo=True)  # Solo activos
    return render(
        request,
        "taller/conductores_lista.html",
        {"conductores": conductores},
    )


# ============================================
# VISTAS PARA CONDUCTORES (CORREGIDAS)
# ============================================

import logging
logger = logging.getLogger(__name__)

def conductor_crear(request):
    """Crea un nuevo conductor y automáticamente crea un usuario con rol Chofer"""
    if request.method == "POST":
        form = ConductorForm(request.POST)
        if form.is_valid():
            conductor = form.save(commit=False)
            
            # Limpiar RUT para usar como username (sin puntos ni guión)
            rut_limpio = conductor.rut.replace('.', '').replace('-', '')
            username = rut_limpio
            password = rut_limpio
            
            # Buscar o crear rol "Chofer"
            rol_chofer, created_rol = Rol.objects.get_or_create(
                nombre='Chofer',
                defaults={'descripcion': 'Rol para conductores que usan la app móvil'}
            )
            
            if created_rol:
                logger.info(f"Rol 'Chofer' creado automáticamente")
            
            # Crear usuario
            user, created_user = User.objects.get_or_create(username=username)
            
            if created_user:
                user.set_password(password)
                user.first_name = conductor.nombres
                user.last_name = conductor.apellidos
                user.email = conductor.email or ''
                user.save()
                logger.info(f"Usuario creado: {username}")
            else:
                logger.info(f"Usuario ya existía: {username}")
            
            # Asignar rol Chofer (si no lo tiene ya)
            usuario_rol, created_ur = UsuarioRol.objects.get_or_create(
                usuario=user,
                defaults={'rol': rol_chofer}
            )
            
            if not created_ur and usuario_rol.rol != rol_chofer:
                usuario_rol.rol = rol_chofer
                usuario_rol.save()
                logger.info(f"Rol actualizado a Chofer para {username}")
            
            # Sincronizar permisos del rol al usuario
            user.user_permissions.set(rol_chofer.permisos.all())
            
            # Vincular conductor con usuario
            conductor.usuario = user
            conductor.save()
            
            if created_user:
                messages.success(
                    request, 
                    f'Conductor creado correctamente. Usuario "{username}" creado con contraseña "{password}". El chofer debe cambiarla al iniciar sesión.'
                )
            else:
                messages.success(
                    request,
                    f'Conductor creado correctamente y vinculado al usuario existente "{username}".'
                )
            
            return redirect("taller_conductores")
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = ConductorForm()
    
    return render(
        request,
        "taller/conductor_form.html",
        {"form": form, "modo": "Crear"},
    )


def conductor_editar(request, pk):
    """Edita un conductor existente y permite gestionar su usuario asociado"""
    conductor = get_object_or_404(Conductor, pk=pk)
    
    if request.method == "POST":
        form = ConductorForm(request.POST, instance=conductor)
        if form.is_valid():
            conductor = form.save()
            
            # Si el conductor no tiene usuario asociado, crearlo
            if not conductor.usuario:
                rut_limpio = conductor.rut.replace('.', '').replace('-', '')
                username = rut_limpio
                password = rut_limpio
                
                rol_chofer, _ = Rol.objects.get_or_create(nombre='Chofer')
                
                user, created = User.objects.get_or_create(username=username)
                if created:
                    user.set_password(password)
                    user.first_name = conductor.nombres
                    user.last_name = conductor.apellidos
                    user.email = conductor.email or ''
                    user.save()
                    messages.info(request, f'Usuario "{username}" creado con contraseña "{password}".')
                else:
                    messages.info(request, f'Vinculado al usuario existente "{username}".')
                
                # Asignar rol Chofer
                UsuarioRol.objects.update_or_create(
                    usuario=user,
                    defaults={'rol': rol_chofer}
                )
                
                # Sincronizar permisos
                user.user_permissions.set(rol_chofer.permisos.all())
                
                conductor.usuario = user
                conductor.save()
            else:
                # Restablecer contraseña si se solicitó
                if request.POST.get('reset_password'):
                    new_password = conductor.rut.replace('.', '').replace('-', '')
                    conductor.usuario.set_password(new_password)
                    conductor.usuario.save()
                    messages.info(request, f'Contraseña restablecida a "{new_password}". El conductor debe cambiarla al iniciar sesión.')
                
                # Actualizar nombre en el usuario si cambió
                if conductor.usuario.first_name != conductor.nombres or conductor.usuario.last_name != conductor.apellidos:
                    conductor.usuario.first_name = conductor.nombres
                    conductor.usuario.last_name = conductor.apellidos
                    conductor.usuario.save()
                    messages.info(request, "Nombre de usuario actualizado.")
            
            messages.success(request, "Conductor actualizado correctamente.")
            return redirect("taller_conductores")
    else:
        form = ConductorForm(instance=conductor)
    
    return render(
        request,
        "taller/conductor_form.html",
        {"form": form, "modo": "Editar", "conductor": conductor},
    )



# ============================================
# VISTAS PARA MANTENIMIENTOS
# ============================================

def mantenimientos_lista(request):
    """Lista mantenimientos con filtros"""
    qs = Mantenimiento.objects.select_related("vehiculo", "taller").all()

    vehiculo_id = request.GET.get("vehiculo")
    tipo = request.GET.get("tipo")
    estado = request.GET.get("estado")
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")

    if vehiculo_id:
        qs = qs.filter(vehiculo_id=vehiculo_id)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if estado:
        qs = qs.filter(estado=estado)
    if desde:
        qs = qs.filter(Q(fecha_programada__gte=desde) | Q(fecha_real__gte=desde))
    if hasta:
        qs = qs.filter(Q(fecha_programada__lte=hasta) | Q(fecha_real__lte=hasta))

    vehiculos = Vehiculo.objects.order_by("patente")

    ctx = {
        "mantenimientos": qs.order_by("-fecha_programada", "-fecha_real", "-id"),
        "vehiculos": vehiculos,
        "f": {
            "vehiculo": vehiculo_id or "",
            "tipo": tipo or "",
            "estado": estado or "",
            "desde": desde or "",
            "hasta": hasta or "",
        },
    }
    return render(request, "taller/mantenimientos_lista.html", ctx)


def mantenimiento_crear(request):
    """Crea un nuevo mantenimiento"""
    if request.method == "POST":
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mantenimiento creado.")
            return redirect("taller_mantenimientos")
    else:
        initial = {}
        vehiculo = request.GET.get("vehiculo")
        if vehiculo:
            initial["vehiculo"] = vehiculo
        form = MantenimientoForm(initial=initial)

    return render(
        request,
        "taller/mantenimiento_form.html",
        {"form": form, "modo": "Crear"},
    )


def mantenimiento_editar(request, pk):
    """Edita un mantenimiento existente y permite agregar repuestos"""
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    repuestos = mantenimiento.repuestos.select_related("producto", "bodega").all().order_by("-id")

    if request.method == "POST":
        accion = request.POST.get("accion", "guardar_mantenimiento")

        if accion == "guardar_repuesto":
            repuesto_form = RepuestoMantenimientoForm(request.POST)
            form = MantenimientoForm(instance=mantenimiento)

            if repuesto_form.is_valid():
                repuesto = repuesto_form.save(commit=False)
                repuesto.mantenimiento = mantenimiento
                repuesto.save()
                messages.success(request, "Repuesto agregado correctamente.")
                return redirect("taller_mantenimiento_editar", pk=mantenimiento.pk)
            else:
                messages.error(request, "No se pudo agregar el repuesto. Revisa los datos.")
        else:
            form = MantenimientoForm(request.POST, instance=mantenimiento)
            repuesto_form = RepuestoMantenimientoForm()

            if form.is_valid():
                mantenimiento = form.save()

                if (
                    mantenimiento.estado == "FINALIZADO"
                    and mantenimiento.km_real
                    and (
                        not mantenimiento.vehiculo.km_actual
                        or mantenimiento.km_real > mantenimiento.vehiculo.km_actual
                    )
                ):
                    mantenimiento.vehiculo.km_actual = mantenimiento.km_real
                    mantenimiento.vehiculo.save(update_fields=["km_actual"])

                messages.success(request, "Mantenimiento actualizado.")
                return redirect("taller_mantenimientos")
    else:
        form = MantenimientoForm(instance=mantenimiento)
        repuesto_form = RepuestoMantenimientoForm()

    mantenimiento.recalcular_costos()
    
    total_repuestos = mantenimiento.repuestos.aggregate(
    total=Sum("costo_total")
)["total"] or 0

    return render(
    request,
    "taller/mantenimiento_form.html",
    {
        "form": form,
        "modo": "Editar",
        "m": mantenimiento,
        "repuesto_form": repuesto_form,
        "repuestos": repuestos,
        "total_repuestos": total_repuestos,
    },
)


def mantenimiento_cambiar_estado(request, pk, nuevo_estado):
    """Cambia el estado de un mantenimiento (acción rápida)"""
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)

    if nuevo_estado not in ["PLANIFICADO", "EN_PROCESO", "FINALIZADO"]:
        messages.error(request, "Estado no válido.")
        return redirect("taller_mantenimientos")

    mantenimiento.estado = nuevo_estado

    if nuevo_estado == "FINALIZADO" and not mantenimiento.fecha_real:
        mantenimiento.fecha_real = timezone.now().date()

    mantenimiento.save()
    messages.success(request, f"Estado actualizado a {nuevo_estado}.")
    return redirect("taller_mantenimientos")


def mantenimiento_repuesto_eliminar(request, pk, repuesto_id):
    """Elimina un repuesto asociado a un mantenimiento"""
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    repuesto = get_object_or_404(
        RepuestoMantenimiento,
        pk=repuesto_id,
        mantenimiento=mantenimiento,
    )

    if request.method == "POST":
        repuesto.delete()
        mantenimiento.recalcular_costos()
        messages.success(request, "Repuesto eliminado del mantenimiento.")
        return redirect("taller_mantenimiento_editar", pk=mantenimiento.pk)

    return redirect("taller_mantenimiento_editar", pk=mantenimiento.pk)


# ============================================
# VISTAS PARA DOCUMENTOS
# ============================================

def _anotar_estado_documentos(qs, campo_fecha="fecha_vencimiento", dias_alerta=30):
    """Anota 'dias_restantes' y 'estado_flag' (0=vencido,1=por_vencer,2=vigente)."""
    hoy = timezone.now().date()
    docs = list(qs)

    for documento in docs:
        fecha_vencimiento = getattr(documento, campo_fecha, None)

        if not fecha_vencimiento:
            documento.dias_restantes = None
            documento.estado_flag = 2
        else:
            documento.dias_restantes = (fecha_vencimiento - hoy).days
            if documento.dias_restantes < 0:
                documento.estado_flag = 0
            elif documento.dias_restantes <= dias_alerta:
                documento.estado_flag = 1
            else:
                documento.estado_flag = 2

    docs.sort(key=lambda x: (x.estado_flag, getattr(x, campo_fecha) or hoy))
    return docs


def documentos_vehiculo_lista(request):
    """Lista documentos de vehículos con filtros"""
    tipo = request.GET.get("tipo") or ""
    estado = request.GET.get("estado") or ""
    vehiculo_id = request.GET.get("vehiculo") or ""

    qs = DocumentoVehiculo.objects.select_related("vehiculo")

    if tipo:
        qs = qs.filter(tipo=tipo)
    if vehiculo_id:
        qs = qs.filter(vehiculo_id=vehiculo_id)

    docs = _anotar_estado_documentos(qs)

    if estado:
        mapa = {"vencido": 0, "por_vencer": 1, "vigente": 2}
        docs = [d for d in docs if d.estado_flag == mapa.get(estado, 2)]

    ctx = {
        "docs": docs,
        "vehiculos": Vehiculo.objects.order_by("patente"),
        "f": {
            "tipo": tipo,
            "estado": estado,
            "vehiculo": vehiculo_id,
        },
    }
    return render(request, "taller/documentos_vehiculos_lista.html", ctx)


def documento_vehiculo_nuevo(request):
    """Crea un nuevo documento de vehículo"""
    if request.method == "POST":
        form = DocumentoVehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de vehículo creado.")
            return redirect("taller_docs_vehiculos")
    else:
        initial = {}
        vehiculo = request.GET.get("vehiculo")
        if vehiculo:
            initial["vehiculo"] = vehiculo
        form = DocumentoVehiculoForm(initial=initial)

    return render(
        request,
        "taller/documento_vehiculo_form.html",
        {"form": form, "modo": "Crear"},
    )


def documento_vehiculo_editar(request, pk):
    """Edita un documento de vehículo existente"""
    doc = get_object_or_404(DocumentoVehiculo, pk=pk)

    if request.method == "POST":
        form = DocumentoVehiculoForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de vehículo actualizado.")
            return redirect("taller_docs_vehiculos")
    else:
        form = DocumentoVehiculoForm(instance=doc)

    return render(
        request,
        "taller/documento_vehiculo_form.html",
        {"form": form, "modo": "Editar", "doc": doc},
    )


def documentos_conductor_lista(request):
    """Lista documentos de conductores con filtros, KPIs e historial por conductor."""
    tipo = request.GET.get("tipo") or ""
    estado = request.GET.get("estado") or ""
    conductor_id = request.GET.get("conductor") or ""

    qs = DocumentoConductor.objects.select_related("conductor")

    if tipo:
        qs = qs.filter(tipo=tipo)

    if conductor_id:
        qs = qs.filter(conductor_id=conductor_id)

    docs = _anotar_estado_documentos(qs)

    for d in docs:
        if d.estado_flag == 0:
            d.estado_doc = "vencido"
        elif d.estado_flag == 1:
            d.estado_doc = "por_vencer"
        else:
            d.estado_doc = "vigente"

    total_vencidos = sum(1 for d in docs if d.estado_doc == "vencido")
    total_por_vencer = sum(1 for d in docs if d.estado_doc == "por_vencer")
    total_vigentes = sum(1 for d in docs if d.estado_doc == "vigente")

    if estado:
        mapa = {"vencido": 0, "por_vencer": 1, "vigente": 2}
        docs = [d for d in docs if d.estado_flag == mapa.get(estado, 2)]

    conductor_actual = None
    historial_conductor = []
    historial_vencidos = 0
    historial_por_vencer = 0
    historial_vigentes = 0

    if conductor_id:
        conductor_actual = Conductor.objects.filter(pk=conductor_id).first()

        if conductor_actual:
            historial_qs = DocumentoConductor.objects.filter(
                conductor=conductor_actual
            ).select_related("conductor")

            historial_conductor = _anotar_estado_documentos(historial_qs)

            for d in historial_conductor:
                if d.estado_flag == 0:
                    d.estado_doc = "vencido"
                elif d.estado_flag == 1:
                    d.estado_doc = "por_vencer"
                else:
                    d.estado_doc = "vigente"

            historial_vencidos = sum(1 for d in historial_conductor if d.estado_doc == "vencido")
            historial_por_vencer = sum(1 for d in historial_conductor if d.estado_doc == "por_vencer")
            historial_vigentes = sum(1 for d in historial_conductor if d.estado_doc == "vigente")

    ctx = {
        "docs": docs,
        "conductores": Conductor.objects.order_by("apellidos", "nombres"),
        "total_vencidos": total_vencidos,
        "total_por_vencer": total_por_vencer,
        "total_vigentes": total_vigentes,
        "conductor_actual": conductor_actual,
        "historial_conductor": historial_conductor,
        "historial_vencidos": historial_vencidos,
        "historial_por_vencer": historial_por_vencer,
        "historial_vigentes": historial_vigentes,
        "f": {
            "tipo": tipo,
            "estado": estado,
            "conductor": conductor_id,
        },
    }
    return render(request, "taller/documentos_conductores_lista.html", ctx)


def documento_conductor_nuevo(request):
    """Crea un nuevo documento de conductor"""
    if request.method == "POST":
        form = DocumentoConductorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de conductor creado.")
            return redirect("taller_docs_conductores")
    else:
        initial = {}
        conductor = request.GET.get("conductor")
        if conductor:
            initial["conductor"] = conductor
        form = DocumentoConductorForm(initial=initial)

    return render(
        request,
        "taller/documento_conductor_form.html",
        {"form": form, "modo": "Crear"},
    )


def documento_conductor_editar(request, pk):
    """Edita un documento de conductor existente"""
    doc = get_object_or_404(DocumentoConductor, pk=pk)

    if request.method == "POST":
        form = DocumentoConductorForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento de conductor actualizado.")
            return redirect("taller_docs_conductores")
    else:
        form = DocumentoConductorForm(instance=doc)

    return render(
        request,
        "taller/documento_conductor_form.html",
        {"form": form, "modo": "Editar", "doc": doc},
    )


# ============================================
# REPORTES DE VEHÍCULOS
# ============================================

def reporte_vehiculo_selector(request):
    """Selector de vehículos para reportes"""
    q = request.GET.get("q", "").strip()
    vehiculos = Vehiculo.objects.all().order_by("patente")

    if q:
        vehiculos = vehiculos.filter(patente__icontains=q)

    return render(
        request,
        "taller/reporte_vehiculo_selector.html",
        {"vehiculos": vehiculos, "q": q},
    )


def _rango_ultimos_12_meses():
    """Genera rango de últimos 12 meses"""
    hoy = timezone.now().date().replace(day=1)
    meses = []
    year, month = hoy.year, hoy.month

    for _ in range(12):
        meses.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1

    meses.reverse()
    return meses


def reporte_vehiculo(request, vehiculo_id: int):
    """Reporte detallado de vehículo"""
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)

    costo_total_expr = ExpressionWrapper(
        Coalesce(F("costo_mano_obra"), 0) + Coalesce(F("costo_repuestos"), 0),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    agg = (
        Mantenimiento.objects.filter(vehiculo=vehiculo)
        .annotate(fecha_ref=Coalesce(F("fecha_real"), F("fecha_programada")))
        .annotate(mes=TruncMonth("fecha_ref"))
        .annotate(costo_calc=costo_total_expr)
        .values("mes")
        .annotate(costo=Sum("costo_calc"))
        .order_by("mes")
    )

    mapa = {
        (a["mes"].year, a["mes"].month): float(a["costo"] or 0)
        for a in agg
        if a["mes"]
    }

    labels, data = [], []
    for year, month in _rango_ultimos_12_meses():
        labels.append(f"{month:02d}-{year}")
        data.append(mapa.get((year, month), 0))

    total_12m = sum(data)
    total_mantenimientos = Mantenimiento.objects.filter(vehiculo=vehiculo).count()

    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)
    docs_qs = DocumentoVehiculo.objects.filter(vehiculo=vehiculo)
    docs_vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    docs_porvencer = docs_qs.filter(
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=limite,
    ).count()
    docs_vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    proximo_preventivo = (
        Mantenimiento.objects.filter(vehiculo=vehiculo, tipo="PREVENTIVO")
        .exclude(fecha_programada__isnull=True)
        .order_by("fecha_programada")
        .first()
    ) or (
        Mantenimiento.objects.filter(vehiculo=vehiculo, tipo="PREVENTIVO")
        .exclude(km_programado__isnull=True)
        .order_by("km_programado")
        .first()
    )

    ctx = {
        "vehiculo": vehiculo,
        "labels": labels,
        "data": data,
        "total_12m": total_12m,
        "total_mantenimientos": total_mantenimientos,
        "docs": {
            "vencidos": docs_vencidos,
            "por_vencer": docs_porvencer,
            "vigentes": docs_vigentes,
            "limite": limite,
        },
        "proximo_preventivo": proximo_preventivo,
    }
    return render(request, "taller/reporte_vehiculo.html", ctx)


def reporte_vehiculo_pdf(request, vehiculo_id: int):
    """Genera PDF del reporte de vehículo"""
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)

    costo_total_expr = ExpressionWrapper(
        Coalesce(F("costo_mano_obra"), 0) + Coalesce(F("costo_repuestos"), 0),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    base_qs = (
        Mantenimiento.objects.filter(vehiculo=vehiculo)
        .annotate(costo_total_calc=costo_total_expr)
    )

    mant_qs = (
        base_qs
        .annotate(fecha_ref=Coalesce(F("fecha_real"), F("fecha_programada")))
        .order_by("-fecha_ref")
    )

    total_mantenimientos = mant_qs.count()

    hace_12_meses = timezone.now().date() - timezone.timedelta(days=365)
    total_12m = float(
        base_qs.filter(
            Q(fecha_real__gte=hace_12_meses) | Q(fecha_programada__gte=hace_12_meses)
        ).aggregate(s=Sum("costo_total_calc"))["s"] or 0
    )

    hoy_1 = timezone.now().date().replace(day=1)
    y_cur, m_cur = hoy_1.year, hoy_1.month
    meses = []
    for _ in range(6):
        meses.append((y_cur, m_cur))
        m_cur -= 1
        if m_cur == 0:
            m_cur = 12
            y_cur -= 1
    meses = list(reversed(meses))

    first_year, first_month = meses[0]
    first_date = date_cls(first_year, first_month, 1)

    agg_mes = (
        base_qs
        .filter(Q(fecha_real__gte=first_date) | Q(fecha_programada__gte=first_date))
        .annotate(mes=TruncMonth(Coalesce("fecha_real", "fecha_programada")))
        .values("mes")
        .annotate(total=Sum("costo_total_calc"))
    )
    mapa_mes = {
        (a["mes"].year, a["mes"].month): float(a["total"] or 0)
        for a in agg_mes
        if a["mes"]
    }

    series_vals = [mapa_mes.get(key, 0) for key in meses]
    max_val = max(series_vals) if series_vals else 1.0

    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)
    docs_qs = DocumentoVehiculo.objects.filter(vehiculo=vehiculo).order_by("fecha_vencimiento")
    docs_vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    docs_porvencer = docs_qs.filter(
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=limite,
    ).count()
    docs_vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    response = HttpResponse(content_type="application/pdf")
    filename = f"reporte_vehiculo_{vehiculo.patente}.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    x = 20 * mm
    y = height - 20 * mm

    logo_path = finders.find("img/logo_transcap.png")
    title_x = x
    if logo_path:
        logo_w = 35 * mm
        logo_h = 15 * mm
        try:
            pdf.drawImage(logo_path, x, y - logo_h + 5 * mm, width=logo_w, height=logo_h, mask="auto")
            title_x = x + logo_w + 5 * mm
        except Exception:
            title_x = x

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(title_x, y, "Transcap ERP - Reporte de Vehículo")
    y -= 10 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(x, y, f"Fecha emisión: {hoy.strftime('%d/%m/%Y')}")
    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Vehículo")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(x, y, f"Patente: {vehiculo.patente}")
    y -= 5 * mm
    pdf.drawString(x, y, f"Marca / Modelo: {vehiculo.marca} {vehiculo.modelo}")
    y -= 5 * mm

    if hasattr(vehiculo, "anio") and vehiculo.anio:
        pdf.drawString(x, y, f"Año: {vehiculo.anio}")
        y -= 5 * mm

    y -= 5 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Resumen de mantenimiento")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        x,
        y,
        f"Costo mantenciones últimos 12 meses: ${int(total_12m):,}".replace(",", "."),
    )
    y -= 5 * mm
    pdf.drawString(x, y, f"Total mantenciones registradas: {total_mantenimientos}")
    y -= 5 * mm
    pdf.drawString(
        x,
        y,
        "Documentos vencidos/por vencer/vigentes: "
        f"{docs_vencidos}/{docs_porvencer}/{docs_vigentes}",
    )
    y -= 10 * mm

    chart_height = 40 * mm
    chart_width = width - 40 * mm
    chart_left = x
    chart_bottom = y - chart_height

    pdf.setLineWidth(0.5)
    pdf.line(chart_left, chart_bottom, chart_left, chart_bottom + chart_height)
    pdf.line(chart_left, chart_bottom, chart_left + chart_width, chart_bottom)

    n = len(meses)
    if n > 0:
        gap = chart_width / (n * 2)
        bar_width = gap
        for idx, val in enumerate(series_vals):
            bar_x = chart_left + gap * (1 + 2 * idx)
            bar_h = (val / max_val) * (chart_height * 0.8)
            pdf.rect(bar_x, chart_bottom, bar_width, bar_h, stroke=1, fill=0)

            mes_label = f"{meses[idx][1]:02d}/{str(meses[idx][0])[-2:]}"
            pdf.setFont("Helvetica", 6)
            pdf.drawCentredString(bar_x + bar_width / 2, chart_bottom - 4 * mm, mes_label)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(chart_left, chart_bottom + chart_height + 3 * mm, "Costo mantenciones últimos 6 meses")

    y = chart_bottom - 10 * mm

    if y < 60 * mm:
        pdf.showPage()
        y = height - 20 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Últimos mantenimientos")
    y -= 6 * mm

    col_fecha_prog = x
    col_fecha_real = x + 30 * mm
    col_tipo = x + 60 * mm
    col_costo = x + 105 * mm
    col_estado = x + 130 * mm

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(col_fecha_prog, y, "Fecha Prog.")
    pdf.drawString(col_fecha_real, y, "Fecha Real")
    pdf.drawString(col_tipo, y, "Tipo")
    pdf.drawString(col_costo, y, "Costo")
    pdf.drawString(col_estado, y, "Estado")
    y -= 4 * mm
    pdf.line(x, y + 2 * mm, width - 20 * mm, y + 2 * mm)
    y -= 2 * mm

    pdf.setFont("Helvetica", 8)

    def _nueva_pagina_mants(y_pos):
        pdf.showPage()
        new_y = height - 20 * mm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x, new_y, "Últimos mantenimientos (cont.)")
        new_y -= 6 * mm

        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(col_fecha_prog, new_y, "Fecha Prog.")
        pdf.drawString(col_fecha_real, new_y, "Fecha Real")
        pdf.drawString(col_tipo, new_y, "Tipo")
        pdf.drawString(col_costo, new_y, "Costo")
        pdf.drawString(col_estado, new_y, "Estado")
        new_y -= 4 * mm
        pdf.line(x, new_y + 2 * mm, width - 20 * mm, new_y + 2 * mm)
        new_y -= 2 * mm
        pdf.setFont("Helvetica", 8)
        return new_y

    for mantenimiento in mant_qs[:10]:
        if y < 30 * mm:
            y = _nueva_pagina_mants(y)

        fecha_prog = mantenimiento.fecha_programada.strftime("%d/%m/%Y") if mantenimiento.fecha_programada else "-"
        fecha_real = mantenimiento.fecha_real.strftime("%d/%m/%Y") if mantenimiento.fecha_real else "-"
        costo_total = int(getattr(mantenimiento, "costo_total_calc", 0) or 0)
        costo_str = f"${costo_total:,}".replace(",", ".")
        tipo_txt = mantenimiento.get_tipo_display() if hasattr(mantenimiento, "get_tipo_display") else mantenimiento.tipo
        estado_txt = mantenimiento.get_estado_display() if hasattr(mantenimiento, "get_estado_display") else getattr(mantenimiento, "estado", "")

        pdf.drawString(col_fecha_prog, y, fecha_prog)
        pdf.drawString(col_fecha_real, y, fecha_real)
        pdf.drawString(col_tipo, y, tipo_txt[:20])
        pdf.drawRightString(col_costo + 20 * mm, y, costo_str)
        pdf.drawString(col_estado, y, estado_txt)
        y -= 4 * mm

        if mantenimiento.descripcion:
            pdf.setFont("Helvetica-Oblique", 7)
            pdf.drawString(col_tipo, y, mantenimiento.descripcion[:80])
            pdf.setFont("Helvetica", 8)
            y -= 4 * mm

    if y < 40 * mm:
        pdf.showPage()
        y = height - 20 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Documentos del vehículo")
    y -= 6 * mm
    pdf.setFont("Helvetica", 9)

    for doc in docs_qs:
        if y < 30 * mm:
            pdf.showPage()
            y = height - 20 * mm
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x, y, "Documentos del vehículo (cont.)")
            y -= 6 * mm
            pdf.setFont("Helvetica", 9)

        tipo_doc = doc.get_tipo_display() if hasattr(doc, "get_tipo_display") else doc.tipo
        emision = doc.fecha_emision.strftime("%d/%m/%Y") if doc.fecha_emision else "-"
        venc = doc.fecha_vencimiento.strftime("%d/%m/%Y") if doc.fecha_vencimiento else "-"

        if doc.fecha_vencimiento and doc.fecha_vencimiento < hoy:
            estado = "VENCIDO"
        elif doc.fecha_vencimiento and doc.fecha_vencimiento <= limite:
            estado = "POR VENCER"
        else:
            estado = "VIGENTE"

        pdf.drawString(x, y, f"- {tipo_doc}: {emision} → {venc}  ({estado})")
        y -= 4 * mm

    pdf.showPage()
    pdf.save()
    return response


# ============================================
# REPORTES DE CONDUCTORES
# ============================================

def reporte_conductor(request, conductor_id: int):
    """Reporte de documentos + multas por conductor"""
    conductor = get_object_or_404(Conductor, pk=conductor_id)

    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)

    docs_qs = DocumentoConductor.objects.filter(conductor=conductor).order_by("fecha_vencimiento")

    vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    por_vencer = docs_qs.filter(
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=limite,
    ).count()
    vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    multas_qs = MultaConductor.objects.filter(conductor=conductor).order_by("-fecha", "-id")
    total_multas = multas_qs.count()
    monto_total = float(multas_qs.aggregate(s=Sum("monto"))["s"] or 0)
    monto_pendiente = float(
        multas_qs.filter(estado="PENDIENTE").aggregate(s=Sum("monto"))["s"] or 0
    )
    ultima_multa = multas_qs.first()

    ctx = {
        "conductor": conductor,
        "docs": docs_qs,
        "vencidos": vencidos,
        "por_vencer": por_vencer,
        "vigentes": vigentes,
        "hoy": hoy,
        "limite": limite,
        "multas": multas_qs,
        "total_multas": total_multas,
        "monto_total": monto_total,
        "monto_pendiente": monto_pendiente,
        "ultima_multa": ultima_multa,
    }

    return render(request, "taller/reporte_conductor.html", ctx)


def reporte_conductor_pdf(request, conductor_id: int):
    """Genera PDF del reporte de conductor"""
    conductor = get_object_or_404(Conductor, pk=conductor_id)

    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=30)

    docs_qs = DocumentoConductor.objects.filter(conductor=conductor).order_by("fecha_vencimiento")

    docs_vencidos = docs_qs.filter(fecha_vencimiento__lt=hoy).count()
    docs_porvencer = docs_qs.filter(
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=limite,
    ).count()
    docs_vigentes = docs_qs.filter(fecha_vencimiento__gt=limite).count()

    response = HttpResponse(content_type="application/pdf")
    filename = f"reporte_conductor_{conductor.rut or conductor.id}.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    x = 20 * mm
    y = height - 20 * mm

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x, y, "Transcap ERP - Reporte de Conductor")
    y -= 10 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(x, y, f"Fecha emisión: {hoy.strftime('%d/%m/%Y')}")
    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Conductor")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    nombre_completo = f"{conductor.apellidos} {conductor.nombres}".strip()
    pdf.drawString(x, y, f"Nombre: {nombre_completo}")
    y -= 5 * mm

    if getattr(conductor, "rut", None):
        pdf.drawString(x, y, f"RUT: {conductor.rut}")
        y -= 5 * mm

    y -= 5 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Resumen de documentos")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        x,
        y,
        f"Documentos vencidos / por vencer / vigentes: "
        f"{docs_vencidos} / {docs_porvencer} / {docs_vigentes}",
    )
    y -= 5 * mm
    pdf.drawString(x, y, f"Rango 'por vencer': hasta {limite.strftime('%d/%m/%Y')}")
    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Detalle de documentos")
    y -= 6 * mm
    pdf.setFont("Helvetica", 9)

    for doc in docs_qs:
        if y < 30 * mm:
            pdf.showPage()
            y = height - 20 * mm
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(x, y, "Detalle de documentos (cont.)")
            y -= 6 * mm
            pdf.setFont("Helvetica", 9)

        tipo_doc = getattr(doc, "get_tipo_display", lambda: doc.tipo)()
        emision = doc.fecha_emision.strftime("%d/%m/%Y") if doc.fecha_emision else "-"
        venc = doc.fecha_vencimiento.strftime("%d/%m/%Y") if doc.fecha_vencimiento else "-"

        if doc.fecha_vencimiento and doc.fecha_vencimiento < hoy:
            estado = "VENCIDO"
        elif doc.fecha_vencimiento and doc.fecha_vencimiento <= limite:
            estado = "POR VENCER"
        else:
            estado = "VIGENTE"

        linea = f"- {tipo_doc}: {emision} → {venc}  ({estado})"
        pdf.drawString(x, y, linea)
        y -= 4 * mm

        if doc.descripcion:
            pdf.drawString(x + 5 * mm, y, doc.descripcion[:90])
            y -= 4 * mm

    pdf.showPage()
    pdf.save()
    return response


def ranking_conductores_multas(request):
    """Ranking de conductores por cantidad de multas"""
    conductores = Conductor.objects.all().order_by("apellidos", "nombres")
    ranking = []

    for conductor in conductores:
        raw_multas = getattr(conductor, "multas", 0)

        if hasattr(raw_multas, "all"):
            total_multas = raw_multas.count()
        else:
            total_multas = raw_multas or 0

        if total_multas <= 0:
            continue

        conductor.total_multas = total_multas
        conductor.monto_total = Decimal("0")
        conductor.monto_pendiente = Decimal("0")
        conductor.ultima_multa = None

        ranking.append(conductor)

    ranking.sort(key=lambda x: x.total_multas, reverse=True)

    return render(
        request,
        "taller/ranking_conductores_multas.html",
        {"ranking": ranking},
    )


def reporte_conductor_selector(request):
    """Selector de conductor para reportes"""
    q = request.GET.get("q", "").strip()

    conductores = Conductor.objects.all().order_by("apellidos", "nombres")

    if q:
        conductores = conductores.filter(
            Q(apellidos__icontains=q)
            | Q(nombres__icontains=q)
            | Q(rut__icontains=q)
        )

    return render(
        request,
        "taller/reporte_conductor_selector.html",
        {"conductores": conductores, "q": q},
    )


# ============================================
# DEBUG TEMPORAL
# ============================================

def debug_vehiculos_tipo(request):
    """Vista temporal para debug - ver vehículos por tipo"""
    tractos = Vehiculo.objects.filter(tipo="TRACTO", activo=True)
    semirremolques = Vehiculo.objects.filter(tipo="SEMIRREMOLQUE", activo=True)
    todos = Vehiculo.objects.all()

    context = {
        "tractos": tractos,
        "semirremolques": semirremolques,
        "todos": todos,
        "tipos_count": Vehiculo.objects.values("tipo").annotate(total=Count("id")),
    }

    return render(request, "taller/debug_vehiculos.html", context)


# ============================================
# MÓDULOS DESHABILITADOS POR MIENTRAS
# ============================================

@login_required
def rutas_viaje_lista(request):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. Las rutas de viaje ya no se administran desde Taller."
    )


@login_required
def rutas_viaje_crear(request):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. Las rutas de viaje ya no se administran desde Taller."
    )


@login_required
def rutas_viaje_editar(request, pk):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. Las rutas de viaje ya no se administran desde Taller."
    )


@login_required
def rutas_viaje_eliminar(request, pk):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. Las rutas de viaje ya no se administran desde Taller."
    )


def get_ruta_detalle(request, ruta_id):
    return JsonResponse(
        {
            "success": False,
            "error": "Módulo deshabilitado por mientras. La ruta ya no se gestiona desde Taller.",
        },
        status=403,
    )


@login_required
def coordinacion_viajes_lista(request):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. La coordinación de viajes ahora se gestiona en otro módulo."
    )


@login_required
def coordinacion_viaje_crear(request):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. La coordinación de viajes ahora se gestiona en otro módulo."
    )


@login_required
def coordinacion_viaje_editar(request, pk):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. La coordinación de viajes ahora se gestiona en otro módulo."
    )


@login_required
def coordinacion_viaje_eliminar(request, pk):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. La coordinación de viajes ahora se gestiona en otro módulo."
    )


@login_required
def coordinacion_viaje_pdf(request, pk):
    return HttpResponseForbidden(
        "Módulo deshabilitado por mientras. La coordinación de viajes ahora se gestiona en otro módulo."
    )


# ============================================
# DASHBOARD TALLER (único)
# ============================================

@login_required
def dashboard_taller(request):
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    proxima_semana = hoy + timezone.timedelta(days=7)

    total = Mantenimiento.objects.count()
    pendientes = Mantenimiento.objects.filter(estado="PENDIENTE").count()
    proceso = Mantenimiento.objects.filter(estado="EN_PROCESO").count()
    finalizados = Mantenimiento.objects.filter(estado="FINALIZADO").count()

    costo_mes = Mantenimiento.objects.filter(
        fecha_programada__gte=inicio_mes
    ).aggregate(total=Sum("costo_total"))["total"] or 0

    alertas_fecha = Mantenimiento.objects.select_related("vehiculo").filter(
        estado__in=["PENDIENTE", "EN_PROCESO"],
        fecha_programada__isnull=False,
        fecha_programada__lte=proxima_semana,
    ).order_by("fecha_programada")[:10]

    alertas_km = Mantenimiento.objects.select_related("vehiculo").filter(
        estado__in=["PENDIENTE", "EN_PROCESO"],
        km_programado__isnull=False,
        vehiculo__km_actual__isnull=False,
        km_programado__lte=F("vehiculo__km_actual") + 1000,
    ).order_by("km_programado")[:10]

    ranking_vehiculos = (
        Mantenimiento.objects
        .values("vehiculo__id", "vehiculo__patente", "vehiculo__marca", "vehiculo__modelo")
        .annotate(
            total_mantenimientos=Count("id"),
            costo_total=Sum("costo_total"),
        )
        .order_by("-costo_total", "-total_mantenimientos")[:10]
    )

    ultimos = (
        Mantenimiento.objects
        .select_related("vehiculo", "taller")
        .order_by("-id")[:10]
    )

    serie_costos = (
        Mantenimiento.objects
        .filter(fecha_programada__isnull=False)
        .annotate(mes=TruncMonth("fecha_programada"))
        .values("mes")
        .annotate(total=Sum("costo_total"), cantidad=Count("id"))
        .order_by("mes")
    )

    labels_meses = [item["mes"].strftime("%m/%Y") if item["mes"] else "" for item in serie_costos]
    data_costos = [float(item["total"] or 0) for item in serie_costos]
    data_cantidad = [int(item["cantidad"] or 0) for item in serie_costos]

    return render(
        request,
        "taller/dashboard.html",
        {
            "total": total,
            "pendientes": pendientes,
            "proceso": proceso,
            "finalizados": finalizados,
            "costo_mes": costo_mes,
            "alertas_fecha": alertas_fecha,
            "alertas_km": alertas_km,
            "ranking_vehiculos": ranking_vehiculos,
            "ultimos": ultimos,
            "labels_meses": labels_meses,
            "data_costos": data_costos,
            "data_cantidad": data_cantidad,
        },
    )