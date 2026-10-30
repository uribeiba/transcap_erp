from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.contrib.auth.models import User

from .models import Documento


# ==============================
# DASHBOARD
# ==============================

@login_required
def dashboard_documentos(request):

    total = Documento.objects.count()

    total_guias = Documento.objects.filter(
        tipo_documento="GUIA"
    ).count()

    total_peajes = Documento.objects.filter(
        tipo_documento="PEAJE"
    ).count()

    total_carga = Documento.objects.filter(
        tipo_documento="CARGA"
    ).count()

    ultimos = Documento.objects.order_by(
        "-fecha_registro"
    )[:10]

    context = {

        "total": total,
        "total_guias": total_guias,
        "total_peajes": total_peajes,
        "total_carga": total_carga,
        "ultimos": ultimos,

    }

    return render(
        request,
        "documentos/dashboard.html",
        context
    )


# ==============================
# CREAR DOCUMENTO MANUAL
# ==============================

@login_required
def crear_documento(request):

    usuarios = User.objects.all()

    if request.method == "POST":

        usuario_id = request.POST.get("usuario")
        tipo = request.POST.get("tipo")
        numero = request.POST.get("numero_documento")
        imagen = request.FILES.get("imagen")

        usuario = get_object_or_404(
            User,
            id=usuario_id
        )

        Documento.objects.create(

            usuario=usuario,
            tipo_documento=tipo,   # 👈 CORREGIDO
            numero_documento=numero,
            imagen=imagen

        )

        messages.success(
            request,
            "Documento registrado correctamente"
        )

        return redirect(
            "documentos:lista"
        )

    context = {

        "usuarios": usuarios

    }

    return render(
        request,
        "documentos/documentos_form.html",
        context
    )


# ==============================
# LISTA DE DOCUMENTOS
# ==============================

@login_required
def lista_documentos(request):

    documentos = Documento.objects.all().order_by(
        "-fecha_registro"
    )

    usuarios = User.objects.all()

    # ======================
    # FILTROS
    # ======================

    usuario_id = request.GET.get(
        "usuario"
    )

    tipo = request.GET.get(
        "tipo"
    )

    fecha_desde = request.GET.get(
        "fecha_desde"
    )

    fecha_hasta = request.GET.get(
        "fecha_hasta"
    )

    if usuario_id:

        documentos = documentos.filter(
            usuario_id=usuario_id
        )

    if tipo:

        documentos = documentos.filter(
            tipo_documento=tipo   # 👈 CORREGIDO
        )

    if fecha_desde:

        fecha = parse_date(
            fecha_desde
        )

        if fecha:

            documentos = documentos.filter(
                fecha_registro__date__gte=fecha
            )

    if fecha_hasta:

        fecha = parse_date(
            fecha_hasta
        )

        if fecha:

            documentos = documentos.filter(
                fecha_registro__date__lte=fecha
            )

    # ======================
    # PAGINACIÓN
    # ======================

    paginator = Paginator(
        documentos,
        10
    )

    page_number = request.GET.get(
        "page"
    )

    documentos = paginator.get_page(
        page_number
    )

    context = {

        "documentos": documentos,
        "usuarios": usuarios,

    }

    return render(
        request,
        "documentos/documentos_list.html",
        context
    )


# ==============================
# ELIMINAR DOCUMENTO
# ==============================

@login_required
def eliminar_documento(request, pk):

    documento = get_object_or_404(
        Documento,
        pk=pk
    )

    documento.delete()

    messages.success(
        request,
        "Documento eliminado correctamente"
    )

    return redirect(
        "documentos:lista"
    )