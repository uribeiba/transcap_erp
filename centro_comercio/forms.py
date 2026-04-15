from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Cliente, Cotizacion, CotizacionItem, Vendedor, CotizacionCuota

# ------------------------------------------------------------
# FORMULARIO DE CLIENTE
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# FORMULARIO DE COTIZACIÓN (CABECERA)
# ------------------------------------------------------------
class CotizacionForm(forms.ModelForm):
    
    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "form-control"}
        ),
        input_formats=["%Y-%m-%d"],
    )

    vigencia_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "form-control"}
        ),
        input_formats=["%Y-%m-%d"],
    )

    class Meta:
        model = Cotizacion
        fields = [
            # "numero",  ← ELIMINADO (no se envía)
            "codigo",
            "cliente",
            "fecha",
            "vigencia_hasta",
            "descuento",
            "terminos",
            "estado",
            "sucursal",
            "vendedor",
            "comision_porcentaje",
            "descuento_porcentaje",
            "recargo_porcentaje",
            "glosa",
            "observaciones",
            "condicion_venta",
        ]
        # ... resto del código

        widgets = {
            "numero": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1"
                }
            ),
            "codigo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "readonly": "readonly"
                }
            ),
            "cliente": forms.Select(
                attrs={"class": "form-control select2-cliente"}
            ),
            "descuento": forms.NumberInput(
                attrs={
                    "class": "form-control descuento-monto",
                    "min": "0",
                    "step": "0.01"
                }
            ),
            "terminos": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "estado": forms.Select(
                attrs={"class": "form-control"}
            ),
            "sucursal": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: MATRIZ"
                }
            ),
            "vendedor": forms.Select(
                attrs={"class": "form-control"}
            ),
            "comision_porcentaje": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01"
                }
            ),
            "descuento_porcentaje": forms.NumberInput(
                attrs={
                    "class": "form-control descuento-porcentaje",
                    "step": "0.01"
                }
            ),
            "recargo_porcentaje": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01"
                }
            ),
            "glosa": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "observaciones": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "condicion_venta": forms.Select(  # NUEVO
                attrs={"class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Control de permisos
        if user and not user.is_superuser:
            if "numero" in self.fields:
                self.fields["numero"].widget = forms.HiddenInput()
                self.fields["numero"].required = False
        else:
            if "numero" in self.fields:
                self.fields["numero"].required = False

        self.fields["codigo"].required = False

        if not self.instance.pk:
            self.fields["codigo"].initial = ""

        fields_to_relax = [
            "sucursal",
            "vendedor",
            "comision_porcentaje",
            "descuento_porcentaje",
            "recargo_porcentaje",
            "glosa",
            "observaciones",
            "descuento",
        ]

        for field in fields_to_relax:
            if field in self.fields:
                self.fields[field].required = False

        if not self.instance.pk:
            self.fields["sucursal"].initial = "MATRIZ"
            self.fields["fecha"].initial = timezone.localdate()
            self.fields["vigencia_hasta"].initial = timezone.localdate()
            self.fields["descuento"].initial = 0
            self.fields["descuento_porcentaje"].initial = 0
            self.fields["recargo_porcentaje"].initial = 0
            self.fields["comision_porcentaje"].initial = 0
            self.fields["condicion_venta"].initial = "CRED"  # NUEVO

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["descuento"] = cleaned_data.get("descuento") or 0
        cleaned_data["descuento_porcentaje"] = cleaned_data.get("descuento_porcentaje") or 0
        cleaned_data["recargo_porcentaje"] = cleaned_data.get("recargo_porcentaje") or 0
        cleaned_data["comision_porcentaje"] = cleaned_data.get("comision_porcentaje") or 0

        fecha = cleaned_data.get("fecha")
        vigencia = cleaned_data.get("vigencia_hasta")

        if fecha and vigencia and vigencia < fecha:
            self.add_error(
                "vigencia_hasta",
                "La fecha de vigencia no puede ser anterior a la fecha de cotización"
            )

        return cleaned_data


# ------------------------------------------------------------
# FORMULARIO DE ÍTEMS
# ------------------------------------------------------------
class CotizacionItemForm(forms.ModelForm):
    exento = forms.ChoiceField(
        choices=[('False', 'No'), ('True', 'Sí')],
        widget=forms.Select(attrs={'class': 'form-control form-control-sm exento-select'}),
        initial='False'
    )
    
    class Meta:
        model = CotizacionItem
        fields = ["titulo", "exento", "unidad", "cantidad", "valor_unitario", "descuento_porcentaje", "descuento"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control form-control-sm item-titulo"}),
            "unidad": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control form-control-sm item-cantidad", "step": "any"}),
            "valor_unitario": forms.NumberInput(attrs={"class": "form-control form-control-sm item-valor", "step": "any"}),
            "descuento_porcentaje": forms.NumberInput(attrs={"class": "form-control form-control-sm item-desc-porc", "step": "0.01"}),
            "descuento": forms.NumberInput(attrs={"class": "form-control form-control-sm item-desc-monto", "step": "any"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["titulo"].required = False
        self.fields["descuento_porcentaje"].required = False
        self.fields["descuento"].required = False
        self.fields["unidad"].required = False
        self.fields["unidad"].initial = "Unidad"

    def clean(self):
        cleaned_data = super().clean()
        titulo = (cleaned_data.get("titulo") or "").strip()
        cantidad = cleaned_data.get("cantidad") or 0
        valor = cleaned_data.get("valor_unitario") or 0
        
        if not titulo and cantidad == 0 and valor == 0:
            return cleaned_data
        
        if (cantidad > 0 or valor > 0) and not titulo:
            self.add_error('titulo', "Debe ingresar una descripción.")
        
        if cantidad < 0:
            self.add_error('cantidad', "La cantidad no puede ser negativa")
        
        if valor < 0:
            self.add_error('valor_unitario', "El valor no puede ser negativo")
        
        return cleaned_data


# ------------------------------------------------------------
# FORMULARIO DE CUOTAS (NUEVO)
# ------------------------------------------------------------
class CotizacionCuotaForm(forms.ModelForm):
    class Meta:
        model = CotizacionCuota
        fields = ["fecha", "monto"]
        widgets = {
            "fecha": forms.DateInput(
                attrs={"type": "date", "class": "form-control form-control-sm"}
            ),
            "monto": forms.NumberInput(
                attrs={"class": "form-control form-control-sm text-right", "step": "any"}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].required = False
        self.fields["monto"].required = False


# ------------------------------------------------------------
# CONFIGURACIÓN DE FORMSETS
# ------------------------------------------------------------
def get_cotizacion_item_formset(extra=1):
    return inlineformset_factory(
        Cotizacion,
        CotizacionItem,
        form=CotizacionItemForm,
        extra=extra,
        can_delete=True,
        validate_min=False,
        min_num=0,
    )


def get_cotizacion_cuota_formset(extra=1):
    """Formset para cuotas de pago"""
    return inlineformset_factory(
        Cotizacion,
        CotizacionCuota,
        form=CotizacionCuotaForm,
        extra=extra,
        can_delete=True,
        validate_min=False,
        min_num=0,
    )


CotizacionItemFormSet = get_cotizacion_item_formset(extra=1)
CotizacionItemFormSetEdit = get_cotizacion_item_formset(extra=0)
CotizacionCuotaFormSet = get_cotizacion_cuota_formset(extra=1)
CotizacionCuotaFormSetEdit = get_cotizacion_cuota_formset(extra=0)