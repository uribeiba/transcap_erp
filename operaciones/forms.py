from django import forms
from .models import EstadoFacturacionGuia


class EstadoFacturacionGuiaForm(forms.ModelForm):
    class Meta:
        model = EstadoFacturacionGuia
        fields = [
            "fecha", "cliente", "origen", "destino",
            "nro_guia", "nro_factura", "referencia_viaje",
            "monto", "estado", "prioridad", "observaciones",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "cliente": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "origen": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "destino": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "nro_guia": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "nro_factura": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "referencia_viaje": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "monto": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "estado": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "prioridad": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2}),
        }
