from django import forms
from django.forms import inlineformset_factory
from .models import EDP, EDPago  # Cambiado de EDPPago a EDPago


class EDPForm(forms.ModelForm):
    class Meta:
        model = EDP
        fields = ["codigo", "fecha_pago", "glosa", "estado"]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_pago": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "glosa": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }


class ServiciosSelectForm(forms.Form):
    servicios = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control select2", "multiple": "multiple"}),
    )

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        super().__init__(*args, **kwargs)
        self.fields["servicios"].choices = choices


class EDPagoForm(forms.ModelForm):  # Cambiado de EDPPagoForm a EDPagoForm
    class Meta:
        model = EDPago  # Cambiado de EDPPago a EDPago
        fields = ["fecha", "medio_pago", "monto", "referencia"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "medio_pago": forms.Select(attrs={"class": "form-control"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "referencia": forms.TextInput(attrs={"class": "form-control"}),
        }

EDPPagoFormSet = inlineformset_factory(
    EDP, EDPago, form=EDPagoForm, extra=1, can_delete=True  # Cambiado EDPPago a EDPago
)