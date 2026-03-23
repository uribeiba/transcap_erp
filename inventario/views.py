from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    BodegaForm,
    FiltroProductoForm,
    MovimientoInventarioForm,
    ProductoForm,
)
from .forms_categoria import CategoriaProductoForm
from .models import (
    Bodega,
    CategoriaProducto,
    MovimientoInventario,
    Producto,
    TipoMovimiento,
)


@login_required
def dashboard_inventario(request):
    hoy = timezone.localdate()
    hace_7_dias = hoy - timedelta(days=7)

    productos_activos_qs = Producto.objects.filter(activo=True).select_related("categoria")
    productos_activos = productos_activos_qs.count()
    total_productos = Producto.objects.count()

    productos_sin_stock = 0
    productos_bajo_minimo_lista = []

    for p in productos_activos_qs:
        stock = p.stock_actual()
        if stock <= 0:
            productos_sin_stock += 1
        elif stock < p.stock_minimo:
            productos_bajo_minimo_lista.append((p, stock))

    productos_bajo_minimo = len(productos_bajo_minimo_lista)

    movimientos_hoy = MovimientoInventario.objects.filter(fecha__date=hoy).count()
    movimientos_ultimos_7 = MovimientoInventario.objects.filter(fecha__date__gte=hace_7_dias).count()

    dias = [hoy - timedelta(days=i) for i in range(6, -1, -1)]
    chart_labels = [d.strftime("%d-%m") for d in dias]
    chart_movimientos = []

    base_qs = MovimientoInventario.objects.all()

    for d in dias:
        total_dia = base_qs.filter(fecha__date=d).aggregate(total=Sum("cantidad"))["total"] or 0
        chart_movimientos.append(float(total_dia))

    top_movimientos = (
        MovimientoInventario.objects.values("producto__codigo", "producto__nombre")
        .annotate(total_mov=Sum("cantidad"))
        .order_by("-total_mov")[:5]
    )

    context = {
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "productos_sin_stock": productos_sin_stock,
        "productos_bajo_minimo": productos_bajo_minimo,
        "movimientos_hoy": movimientos_hoy,
        "movimientos_ultimos_7": movimientos_ultimos_7,
        "top_movimientos": top_movimientos,
        "productos_bajo_minimo_lista": productos_bajo_minimo_lista,
        "chart_labels": chart_labels,
        "chart_movimientos": chart_movimientos,
    }
    return render(request, "inventario/dashboard.html", context)


@login_required
def lista_productos(request):
    productos = Producto.objects.all().select_related("categoria")
    filtro_form = FiltroProductoForm(request.GET or None)

    if filtro_form.is_valid():
        buscar = filtro_form.cleaned_data.get("buscar")
        categoria = filtro_form.cleaned_data.get("categoria")
        estado_stock = filtro_form.cleaned_data.get("estado_stock")

        if buscar:
            productos = productos.filter(
                models.Q(codigo__icontains=buscar) |
                models.Q(nombre__icontains=buscar)
            )

        if categoria:
            productos = productos.filter(categoria=categoria)

        productos = list(productos)

        if estado_stock:
            filtrados = []
            for producto in productos:
                stock = producto.stock_actual()

                if estado_stock == "sin_stock" and stock <= 0:
                    filtrados.append(producto)
                elif estado_stock == "bajo_minimo" and stock > 0 and stock < producto.stock_minimo:
                    filtrados.append(producto)
                elif estado_stock == "ok" and stock >= producto.stock_minimo:
                    filtrados.append(producto)

            productos = filtrados

    context = {
        "productos": productos,
        "filtro_form": filtro_form,
    }
    return render(request, "inventario/lista_productos.html", context)


@login_required
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect("inventario:lista_productos")
    else:
        form = ProductoForm()

    context = {
        "form": form,
        "producto": None,
    }
    return render(request, "inventario/producto_form.html", context)


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("inventario:lista_productos")
    else:
        form = ProductoForm(instance=producto)

    context = {
        "form": form,
        "producto": producto,
    }
    return render(request, "inventario/producto_form.html", context)


@login_required
def lista_movimientos(request):
    movimientos = MovimientoInventario.objects.select_related(
        "producto", "bodega", "usuario_registro"
    ).all()

    producto_id = request.GET.get("producto")
    tipo = request.GET.get("tipo")

    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)

    context = {
        "movimientos": movimientos,
    }
    return render(request, "inventario/lista_movimientos.html", context)


@login_required
def registrar_movimiento(request):
    total_bodegas_activas = Bodega.objects.filter(activa=True).count()

    if request.method == "POST":
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.usuario_registro = request.user
            movimiento.save()
            messages.success(request, "Movimiento registrado y stock actualizado.")
            return redirect("inventario:lista_movimientos")
        messages.error(request, "No se pudo guardar el movimiento. Revisa los campos marcados.")
    else:
        form = MovimientoInventarioForm()

    context = {
        "form": form,
        "sin_bodegas": total_bodegas_activas == 0,
    }
    return render(request, "inventario/movimiento_form.html", context)


@login_required
def lista_bodegas(request):
    bodegas = Bodega.objects.all().order_by("nombre")
    context = {
        "bodegas": bodegas,
    }
    return render(request, "inventario/bodegas_lista.html", context)


@login_required
def crear_bodega(request):
    if request.method == "POST":
        form = BodegaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Bodega creada correctamente.")
            return redirect("inventario:lista_bodegas")
    else:
        form = BodegaForm()

    context = {
        "form": form,
        "bodega": None,
    }
    return render(request, "inventario/bodega_form.html", context)


@login_required
def editar_bodega(request, pk):
    bodega = get_object_or_404(Bodega, pk=pk)

    if request.method == "POST":
        form = BodegaForm(request.POST, instance=bodega)
        if form.is_valid():
            form.save()
            messages.success(request, "Bodega actualizada correctamente.")
            return redirect("inventario:lista_bodegas")
    else:
        form = BodegaForm(instance=bodega)

    context = {
        "form": form,
        "bodega": bodega,
    }
    return render(request, "inventario/bodega_form.html", context)


@login_required
def lista_categorias(request):
    categorias = CategoriaProducto.objects.all().order_by("nombre")
    context = {
        "categorias": categorias,
    }
    return render(request, "inventario/categorias_lista.html", context)


@login_required
def crear_categoria(request):
    if request.method == "POST":
        form = CategoriaProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("inventario:lista_categorias")
    else:
        form = CategoriaProductoForm()

    context = {
        "form": form,
        "categoria": None,
    }
    return render(request, "inventario/categoria_form.html", context)


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProducto, pk=pk)
    if request.method == "POST":
        form = CategoriaProductoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("inventario:lista_categorias")
    else:
        form = CategoriaProductoForm(instance=categoria)

    context = {
        "form": form,
        "categoria": categoria,
    }
    return render(request, "inventario/categoria_form.html", context)


@login_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProducto, pk=pk)

    if request.method == "POST":
        categoria.delete()
        messages.success(request, "Categoría eliminada correctamente.")
        return redirect("inventario:lista_categorias")

    context = {
        "categoria": categoria,
    }
    return render(request, "inventario/categoria_confirmar_eliminar.html", context)


def _build_kardex_rows(producto, fecha_desde=None, fecha_hasta=None):
    movimientos_qs = (
        MovimientoInventario.objects
        .filter(producto=producto)
        .select_related("bodega", "usuario_registro")
    )

    if fecha_desde:
        movimientos_qs = movimientos_qs.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        movimientos_qs = movimientos_qs.filter(fecha__date__lte=fecha_hasta)

    movimientos_qs = movimientos_qs.order_by("fecha", "pk")

    saldo = 0
    kardex_rows = []

    for mov in movimientos_qs:
        if mov.tipo == TipoMovimiento.INGRESO:
            saldo += mov.cantidad
        elif mov.tipo == TipoMovimiento.SALIDA:
            saldo -= mov.cantidad
        elif mov.tipo == TipoMovimiento.AJUSTE:
            saldo = mov.cantidad

        kardex_rows.append({"mov": mov, "saldo": saldo})

    return kardex_rows


@login_required
def kardex_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    fecha_desde = request.GET.get("desde") or None
    fecha_hasta = request.GET.get("hasta") or None

    kardex_rows = _build_kardex_rows(producto, fecha_desde, fecha_hasta)

    context = {
        "producto": producto,
        "kardex_rows": kardex_rows,
        "fecha_desde": fecha_desde or "",
        "fecha_hasta": fecha_hasta or "",
    }
    return render(request, "inventario/kardex_producto.html", context)


@login_required
def kardex_producto_print(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    fecha_desde = request.GET.get("desde") or None
    fecha_hasta = request.GET.get("hasta") or None

    kardex_rows = _build_kardex_rows(producto, fecha_desde, fecha_hasta)

    context = {
        "producto": producto,
        "kardex_rows": kardex_rows,
        "fecha_desde": fecha_desde or "",
        "fecha_hasta": fecha_hasta or "",
    }
    return render(request, "inventario/kardex_producto_print.html", context)