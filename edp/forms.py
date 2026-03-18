from django import forms
from django.forms import inlineformset_factory

from bitacora.models import Bitacora
from centro_comercio.models import Cliente
from .models import EDP, EDPServicio, EDPago


class EDPForm(forms.ModelForm):
    class Meta:
        model = EDP
        fields = [
            "codigo",
            "cliente",
            "fecha_pago",
            "fecha_inicio",
            "fecha_termino",
            "responsable",
            "glosa",
            "estado",
        ]
        widgets = {
            "codigo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Código EDP",
                    "readonly": "readonly",
                }
            ),
            "cliente": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "fecha_pago": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "fecha_inicio": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "fecha_termino": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "responsable": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Responsable del EDP",
                }
            ),
            "glosa": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observación, nota o glosa del EDP...",
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }
        labels = {
            "codigo": "Código EDP",
            "cliente": "Cliente",
            "fecha_pago": "Fecha documento",
            "fecha_inicio": "Fecha inicio",
            "fecha_termino": "Fecha término",
            "responsable": "Responsable",
            "glosa": "Glosa / Observaciones",
            "estado": "Estado",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cliente"].queryset = Cliente.objects.all().order_by("razon_social")
        self.fields["cliente"].required = False
        self.fields["codigo"].required = False

        if not self.instance.pk and not self.initial.get("codigo"):
            self.fields["codigo"].initial = ""

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_termino = cleaned_data.get("fecha_termino")

        if fecha_inicio and fecha_termino and fecha_inicio > fecha_termino:
            self.add_error("fecha_termino", "La fecha término no puede ser menor que la fecha inicio.")

        return cleaned_data


class ServiciosSelectForm(forms.Form):
    """
    Se mantiene este nombre porque views.py ya lo usa.
    Aunque el step se llama 'servicios', realmente aquí
    seleccionamos registros de Bitácora.
    """
    servicios = forms.MultipleChoiceField(
        required=False,
        label="Servicios operativos / Bitácora",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        super().__init__(*args, **kwargs)
        self.fields["servicios"].choices = choices


class EDPServicioForm(forms.ModelForm):
    class Meta:
        model = EDPServicio
        fields = ["servicio", "tarifa", "estadia"]
        widgets = {
            "servicio": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "tarifa": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0",
                }
            ),
            "estadia": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0",
                }
            ),
        }
        labels = {
            "servicio": "Bitácora",
            "tarifa": "Tarifa flete",
            "estadia": "Estadía / Sobrestadía",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["servicio"].queryset = (
            Bitacora.objects.select_related("cliente")
            .order_by("-fecha", "-id")
        )
        self.fields["servicio"].label_from_instance = self.label_bitacora

    def label_bitacora(self, obj):
        cliente = obj.cliente.razon_social if obj.cliente else "Sin cliente"
        fecha = obj.fecha.strftime("%d/%m/%Y") if obj.fecha else "--/--/----"
        origen = obj.origen or "-"
        destino = obj.destino or "-"
        return f"BIT-{obj.id} | {cliente} | {origen} → {destino} | {fecha}"


class EDPagoForm(forms.ModelForm):
    class Meta:
        model = EDPago
        fields = ["fecha", "medio_pago", "monto", "referencia"]
        widgets = {
            "fecha": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "medio_pago": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "monto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0",
                }
            ),
            "referencia": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "N° transferencia, comprobante o referencia",
                }
            ),
        }
        labels = {
            "fecha": "Fecha",
            "medio_pago": "Medio de pago",
            "monto": "Monto",
            "referencia": "Referencia",
        }


EDPServicioFormSet = inlineformset_factory(
    parent_model=EDP,
    model=EDPServicio,
    form=EDPServicioForm,
    fields=["servicio", "tarifa", "estadia"],
    extra=1,
    can_delete=True,
)


EDPPagoFormSet = inlineformset_factory(
    parent_model=EDP,
    model=EDPago,
    form=EDPagoForm,
    fields=["fecha", "medio_pago", "monto", "referencia"],
    extra=1,
    can_delete=True,
)