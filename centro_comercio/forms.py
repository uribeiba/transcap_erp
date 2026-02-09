from django import forms
from django.forms import inlineformset_factory

from .models import Cliente, Cotizacion, CotizacionItem


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["rut", "razon_social", "giro", "telefono", "email", "direccion", "localidad", "activo"]
        widgets = {
            "rut": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "razon_social": forms.TextInput(attrs={"class": "form-control"}),
            "giro": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "localidad": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_rut(self):
        rut = (self.cleaned_data.get("rut") or "").strip().replace(".", "")
        rut = rut.upper()
        if "-" not in rut and len(rut) >= 8:
            rut = rut[:-1] + "-" + rut[-1]
        return rut


class CotizacionForm(forms.ModelForm):
    # 👇 clave para type="date"
    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d"],
    )
    vigencia_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d"],
    )

    class Meta:
        model = Cotizacion
        fields = ["codigo", "cliente", "fecha", "vigencia_hasta", "descuento", "terminos", "estado"]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "descuento": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "1"}),
            "terminos": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }


class CotizacionItemForm(forms.ModelForm):
    # ✅ CAMBIO: Reemplazar Checkbox con Select para el campo exento
    exento = forms.ChoiceField(
        choices=[(True, 'Sí'), (False, 'No')],
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
        initial=False,
        label="¿Exento?"
    )

    class Meta:
        model = CotizacionItem
        fields = ["titulo", "exento", "unidad", "cantidad", "valor_unitario"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            # "exento": forms.CheckboxInput(attrs={"class": "form-check-input"}),  # ❌ Eliminado
            "unidad": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": "0", "step": "1"}),
            "valor_unitario": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": "0", "step": "1"}),
        }
    
    def clean_exento(self):
        # ✅ Convertir el valor del select ('True'/'False') a booleano
        value = self.cleaned_data.get('exento')
        if isinstance(value, str):
            return value == 'True'
        return bool(value)


CotizacionItemFormSet = inlineformset_factory(
    Cotizacion,
    CotizacionItem,
    form=CotizacionItemForm,
    extra=1,
    can_delete=True
)