from django import forms
from django.utils import timezone
from .models import Bitacora


class BitacoraForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # ✅ compatibilidad: si la vista pasa user=..., no revienta
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Fecha por defecto
        if not self.initial.get('fecha'):
            self.initial['fecha'] = timezone.localdate()

    class Meta:
        model = Bitacora
        fields = [
            "fecha",
            "tracto",
            "rampla",
            "cliente",
            "guias_raw",
            "oc_edp_raw",
            "origen",
            "intermedio",
            "destino",
            "fecha_arribo",
            "fecha_descarga",
            "conductor",
            "coordinador",
            "tarifa_flete",
            "estadia",
            "descripcion_trabajo",
            "estado",
        ]

        widgets = {
            "fecha": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "tracto": forms.Select(attrs={
                "class": "form-control select2-tracto",
            }),
            "rampla": forms.Select(attrs={
                "class": "form-control select2-rampla",
            }),
            "cliente": forms.Select(attrs={
                "class": "form-control select2-cliente",
            }),
            "conductor": forms.Select(attrs={
                "class": "form-control select2-conductor",
            }),
            "guias_raw": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 3291-3292-3293"
            }),
            "oc_edp_raw": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 3291-3292"
            }),
            "origen": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Santiago"
            }),
            "intermedio": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Opcional"
            }),
            "destino": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: CENTINELLA"
            }),
            "fecha_arribo": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "fecha_descarga": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            # ✅ Placeholder solicitado
            "coordinador": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Adolfo Aguilera",
                "autocomplete": "off",
            }),

            "tarifa_flete": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "estadia": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "descripcion_trabajo": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Descripción del trabajo..."
            }),
            "estado": forms.Select(attrs={
                "class": "form-control"
            }),
        }
