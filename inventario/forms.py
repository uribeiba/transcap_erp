from decimal import Decimal

from django import forms

from .models import (
    Bodega,
    CategoriaProducto,
    MovimientoInventario,
    Producto,
    TipoMovimiento,
)


FORM_CONTROL = "form-control"
FORM_CONTROL_SM = "form-control form-control-sm"
EMPTY_LABEL = "---------"


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "codigo",
            "nombre",
            "categoria",
            "unidad_medida",
            "stock_minimo",
            "activo",
            "descripcion",
        ]
        widgets = {
            "codigo": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL,
                    "placeholder": "Ej: PROD-0001",
                    "autocomplete": "off",
                }
            ),
            "nombre": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL,
                    "placeholder": "Nombre del producto",
                    "autocomplete": "off",
                }
            ),
            "categoria": forms.Select(attrs={"class": FORM_CONTROL}),
            "unidad_medida": forms.Select(attrs={"class": FORM_CONTROL}),
            "stock_minimo": forms.NumberInput(
                attrs={
                    "class": FORM_CONTROL,
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "descripcion": forms.Textarea(
                attrs={
                    "class": FORM_CONTROL,
                    "rows": 3,
                    "placeholder": "Descripción opcional del producto",
                }
            ),
        }
        labels = {
            "codigo": "Código",
            "nombre": "Nombre",
            "categoria": "Categoría",
            "unidad_medida": "Unidad de medida",
            "stock_minimo": "Stock mínimo",
            "activo": "Activo",
            "descripcion": "Descripción",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "categoria" in self.fields:
            self.fields["categoria"].queryset = CategoriaProducto.objects.all().order_by("nombre")
            self.fields["categoria"].empty_label = EMPTY_LABEL

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip().upper()
        if not codigo:
            raise forms.ValidationError("Debes ingresar un código.")
        return codigo

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        if not nombre:
            raise forms.ValidationError("Debes ingresar un nombre.")
        return nombre

    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get("stock_minimo")
        if stock_minimo in (None, ""):
            return Decimal("0")
        if stock_minimo < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return stock_minimo


class BodegaForm(forms.ModelForm):
    class Meta:
        model = Bodega
        fields = [
            "nombre",
            "ubicacion",
            "descripcion",
            "activa",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL,
                    "placeholder": "Ej: Bodega Principal",
                    "autocomplete": "off",
                }
            ),
            "ubicacion": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL,
                    "placeholder": "Ej: Patio central / Oficina / Taller",
                    "autocomplete": "off",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": FORM_CONTROL,
                    "rows": 3,
                    "placeholder": "Descripción opcional",
                }
            ),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "nombre": "Nombre",
            "ubicacion": "Ubicación",
            "descripcion": "Descripción",
            "activa": "Activa",
        }

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        if not nombre:
            raise forms.ValidationError("Debes ingresar un nombre para la bodega.")
        return nombre


class FiltroProductoForm(forms.Form):
    buscar = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Código / Nombre",
                "class": FORM_CONTROL_SM,
                "autocomplete": "off",
            }
        ),
    )
    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=CategoriaProducto.objects.all().order_by("nombre"),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={"class": FORM_CONTROL_SM}),
    )
    estado_stock = forms.ChoiceField(
        label="Estado stock",
        required=False,
        choices=(
            ("", "Todos"),
            ("sin_stock", "Sin stock"),
            ("bajo_minimo", "Bajo mínimo"),
            ("ok", "OK"),
        ),
        widget=forms.Select(attrs={"class": FORM_CONTROL_SM}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "categoria" in self.fields:
            self.fields["categoria"].queryset = CategoriaProducto.objects.all().order_by("nombre")


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = [
            "tipo",
            "producto",
            "bodega",
            "cantidad",
            "costo_unitario",
            "referencia",
            "observacion",
        ]
        widgets = {
            "tipo": forms.Select(attrs={"class": FORM_CONTROL}),
            "producto": forms.Select(attrs={"class": FORM_CONTROL}),
            "bodega": forms.Select(attrs={"class": FORM_CONTROL}),
            "cantidad": forms.NumberInput(
                attrs={
                    "class": FORM_CONTROL,
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "costo_unitario": forms.NumberInput(
                attrs={
                    "class": FORM_CONTROL,
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Opcional",
                }
            ),
            "referencia": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL,
                    "placeholder": "Ej: Factura, OT, viaje, ajuste",
                    "autocomplete": "off",
                }
            ),
            "observacion": forms.Textarea(
                attrs={
                    "class": FORM_CONTROL,
                    "rows": 3,
                    "placeholder": "Detalle del movimiento",
                }
            ),
        }
        labels = {
            "tipo": "Tipo",
            "producto": "Producto",
            "bodega": "Bodega",
            "cantidad": "Cantidad",
            "costo_unitario": "Costo unitario",
            "referencia": "Referencia",
            "observacion": "Observación",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "producto" in self.fields:
            self.fields["producto"].queryset = (
                Producto.objects.filter(activo=True)
                .select_related("categoria")
                .order_by("nombre")
            )
            self.fields["producto"].empty_label = EMPTY_LABEL

        if "bodega" in self.fields:
            self.fields["bodega"].queryset = Bodega.objects.filter(activa=True).order_by("nombre")
            self.fields["bodega"].empty_label = EMPTY_LABEL

    def clean_referencia(self):
        referencia = (self.cleaned_data.get("referencia") or "").strip()
        return referencia

    def clean_observacion(self):
        observacion = (self.cleaned_data.get("observacion") or "").strip()
        return observacion

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get("cantidad")
        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero.")
        return cantidad

    def clean_costo_unitario(self):
        costo_unitario = self.cleaned_data.get("costo_unitario")
        if costo_unitario in ("", None):
            return costo_unitario
        if costo_unitario < 0:
            raise forms.ValidationError("El costo unitario no puede ser negativo.")
        return costo_unitario

    def clean(self):
        cleaned_data = super().clean()

        tipo = cleaned_data.get("tipo")
        producto = cleaned_data.get("producto")
        bodega = cleaned_data.get("bodega")
        cantidad = cleaned_data.get("cantidad")

        if not tipo or not producto or not bodega or cantidad is None:
            return cleaned_data

        tipo_valor = getattr(tipo, "value", tipo)

        if tipo_valor == getattr(TipoMovimiento, "SALIDA", "SAL"):
            stock_actual = producto.stock_actual(bodega=bodega) or Decimal("0")
            if cantidad > stock_actual:
                self.add_error(
                    "cantidad",
                    f"No hay stock suficiente en la bodega seleccionada. Stock actual: {stock_actual}."
                )

        return cleaned_data