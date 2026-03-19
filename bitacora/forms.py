from django import forms
from django.utils import timezone
from .models import Bitacora


class BitacoraForm(forms.ModelForm):
    # ---------------------------------------------------------
    # Campos de fecha con formato HTML5 compatible.
    # Esto evita que el navegador muestre los date inputs vacíos
    # cuando Django intenta renderizar con formato local (es-cl).
    # ---------------------------------------------------------
    fecha = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "class": "form-control"
            }
        ),
    )

    fecha_arribo = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "class": "form-control"
            }
        ),
    )

    fecha_descarga = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "class": "form-control"
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        # Compatibilidad por si la vista pasa user=...
        kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # ---------------------------------------------------------
        # Solo ponemos fecha por defecto si realmente es creación
        # y no existe valor previo en la instancia.
        # ---------------------------------------------------------
        if not self.instance.pk and not self.initial.get("fecha"):
            self.initial["fecha"] = timezone.localdate()

        # Etiquetas más claras según tu flujo real
        self.fields["fecha"].label = "Fecha"
        self.fields["fecha_arribo"].label = "Fecha carga"
        self.fields["fecha_descarga"].label = "Fecha descarga"

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