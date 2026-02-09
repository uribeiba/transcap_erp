from django import forms
from .models import Producto, MovimientoInventario, CategoriaProducto, Bodega


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
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "categoria": forms.Select(attrs={"class": "form-control"}),
            "unidad_medida": forms.Select(attrs={"class": "form-control"}),
            "stock_minimo": forms.NumberInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "descripcion": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class FiltroProductoForm(forms.Form):
    buscar = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Código / Nombre",
                "class": "form-control form-control-sm",
            }
        ),
    )
    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=CategoriaProducto.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={"class": "form-control form-control-sm"}),
    )


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
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "producto": forms.Select(attrs={"class": "form-control"}),
            "bodega": forms.Select(attrs={"class": "form-control"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control"}),
            "costo_unitario": forms.NumberInput(attrs={"class": "form-control"}),
            "referencia": forms.TextInput(attrs={"class": "form-control"}),
            "observacion": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data["cantidad"]
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero.")
        return cantidad
