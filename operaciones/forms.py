from django import forms

from .models import EstadoFacturacionGuia
from .models import EstatusOperacionalViaje, TurnoEstatus


class EstadoFacturacionGuiaForm(forms.ModelForm):
    fecha = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
    )

    class Meta:
        model = EstadoFacturacionGuia
        fields = [
            "fecha", "cliente", "origen", "destino",
            "nro_guia", "nro_factura", "referencia_viaje",
            "monto", "estado", "prioridad", "observaciones",
        ]
        widgets = {
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


class EstatusOperacionalViajeForm(forms.ModelForm):
    # ---------------------------------------------------------
    # Fechas con formato HTML5 compatible.
    # Dejamos esto explícito para evitar valores vacíos al editar
    # cuando el locale de Django intenta usar dd/mm/yyyy.
    # ---------------------------------------------------------
    fecha = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
    )

    fecha_carga = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
    )

    fecha_descarga = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"class": "form-control form-control-sm", "type": "date"}
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
            "turno": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "conductor": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "tracto": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "rampla": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "cliente": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "nro_guia": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "N° guía"}),
            "estado_guia": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Estado guía"}),
            "estado_carga": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "lugar_carga": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Lugar de carga"}),
            "lugar_descarga": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Lugar de descarga"}),
            "estado_texto": forms.Textarea(
                attrs={
                    "class": "form-control form-control-sm",
                    "rows": 2,
                    "placeholder": "Ej: CAMINO A DESCARGAR / DESCARGADO / RETORNO..."
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control form-control-sm",
                    "rows": 2,
                    "placeholder": "Observaciones adicionales..."
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_carga = cleaned_data.get("fecha_carga")
        fecha_descarga = cleaned_data.get("fecha_descarga")

        # Validación simple para mantener coherencia del viaje
        if fecha_carga and fecha_descarga and fecha_descarga < fecha_carga:
            self.add_error("fecha_descarga", "La fecha de descarga no puede ser menor a la fecha de carga.")

        return cleaned_data