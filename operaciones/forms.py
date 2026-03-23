from django import forms

from .models import EstadoFacturacionGuia, EstatusOperacionalViaje, TurnoEstatus


FORM_CONTROL_SM = "form-control form-control-sm"


class EstadoFacturacionGuiaForm(forms.ModelForm):
    fecha = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": FORM_CONTROL_SM,
                "type": "date",
            },
        ),
    )

    class Meta:
        model = EstadoFacturacionGuia
        fields = [
            "fecha",
            "cliente",
            "origen",
            "destino",
            "nro_guia",
            "nro_factura",
            "referencia_viaje",
            "monto",
            "estado",
            "prioridad",
            "observaciones",
        ]
        widgets = {
            "cliente": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "origen": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "destino": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "nro_guia": forms.TextInput(attrs={"class": FORM_CONTROL_SM}),
            "nro_factura": forms.TextInput(attrs={"class": FORM_CONTROL_SM}),
            "referencia_viaje": forms.TextInput(attrs={"class": FORM_CONTROL_SM}),
            "monto": forms.NumberInput(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "step": "0.01",
                }
            ),
            "estado": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "prioridad": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "observaciones": forms.Textarea(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "rows": 2,
                }
            ),
        }


class EstatusOperacionalViajeForm(forms.ModelForm):
    fecha = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": FORM_CONTROL_SM,
                "type": "date",
            },
        ),
    )

    fecha_carga = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": FORM_CONTROL_SM,
                "type": "date",
            },
        ),
    )

    fecha_descarga = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": FORM_CONTROL_SM,
                "type": "date",
            },
        ),
    )

    class Meta:
        model = EstatusOperacionalViaje
        fields = [
            "fecha",
            "turno",
            "conductor",
            "tracto",
            "rampla",
            "cliente",
            "nro_guia",
            "estado_guia",
            "estado_carga",
            "lugar_carga",
            "fecha_carga",
            "lugar_descarga",
            "fecha_descarga",
            "estado_texto",
            "observaciones",
        ]
        widgets = {
            "turno": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "conductor": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "tracto": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "rampla": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "cliente": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "nro_guia": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "placeholder": "N° guía",
                }
            ),
            "estado_guia": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "placeholder": "Estado guía",
                }
            ),
            "estado_carga": forms.Select(attrs={"class": FORM_CONTROL_SM}),
            "lugar_carga": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "placeholder": "Lugar de carga",
                }
            ),
            "lugar_descarga": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "placeholder": "Lugar de descarga",
                }
            ),
            "estado_texto": forms.Textarea(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "rows": 2,
                    "placeholder": "Ej: CAMINO A DESCARGAR / DESCARGADO / RETORNO...",
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": FORM_CONTROL_SM,
                    "rows": 2,
                    "placeholder": "Observaciones adicionales...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "turno" in self.fields:
            self.fields["turno"].choices = TurnoEstatus.choices

    def clean(self):
        cleaned_data = super().clean()
        fecha_carga = cleaned_data.get("fecha_carga")
        fecha_descarga = cleaned_data.get("fecha_descarga")

        if fecha_carga and fecha_descarga and fecha_descarga < fecha_carga:
            self.add_error(
                "fecha_descarga",
                "La fecha de descarga no puede ser menor a la fecha de carga.",
            )

        return cleaned_data