from django import forms
from django.apps import apps

from .models import (
    Vehiculo,
    Conductor,
    Remolque,
    Taller,
    DocumentoVehiculo,
    DocumentoConductor,
    Mantenimiento,
    MultaConductor,
    RutaViaje,
    CoordinacionViaje,
    RepuestoMantenimiento,
)


FORM_CONTROL = "form-control"
FORM_CHECK = "form-check-input"


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = "__all__"
        widgets = {
            "patente": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "marca": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "modelo": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "anio": forms.NumberInput(attrs={"class": FORM_CONTROL}),
            "tipo": forms.Select(attrs={"class": FORM_CONTROL}),
            "km_actual": forms.NumberInput(attrs={"class": FORM_CONTROL}),
            "nro_motor": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "nro_chasis": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "capacidad": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "fecha_compra": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "aseguradora": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "descripcion_equipo": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "estado_equipo": forms.Select(attrs={"class": FORM_CONTROL}),
            "tipo_remolque": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "estado": forms.Select(attrs={"class": FORM_CONTROL}),
            "activo": forms.CheckboxInput(attrs={"class": FORM_CHECK}),
        }


class ConductorForm(forms.ModelForm):
    class Meta:
        model = Conductor
        fields = "__all__"
        widgets = {
            "rut": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "nombres": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "apellidos": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "telefono": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "email": forms.EmailInput(attrs={"class": FORM_CONTROL}),
            "fecha_ingreso": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "licencia_clase": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "licencia_vencimiento": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": FORM_CHECK}),
        }


class RemolqueForm(forms.ModelForm):
    class Meta:
        model = Remolque
        fields = "__all__"
        widgets = {
            "codigo": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "patente": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "descripcion": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "activo": forms.CheckboxInput(attrs={"class": FORM_CHECK}),
        }


class TallerForm(forms.ModelForm):
    class Meta:
        model = Taller
        fields = "__all__"
        widgets = {
            "nombre": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "ubicacion": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "telefono": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "email": forms.EmailInput(attrs={"class": FORM_CONTROL}),
            "activo": forms.CheckboxInput(attrs={"class": FORM_CHECK}),
        }


class DocumentoVehiculoForm(forms.ModelForm):
    class Meta:
        model = DocumentoVehiculo
        fields = "__all__"
        widgets = {
            "vehiculo": forms.Select(attrs={"class": FORM_CONTROL}),
            "tipo": forms.Select(attrs={"class": FORM_CONTROL}),
            "descripcion": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "fecha_emision": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "fecha_vencimiento": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "archivo": forms.ClearableFileInput(attrs={"class": FORM_CONTROL}),
        }


class DocumentoConductorForm(forms.ModelForm):
    class Meta:
        model = DocumentoConductor
        fields = "__all__"
        widgets = {
            "conductor": forms.Select(attrs={"class": FORM_CONTROL}),
            "tipo": forms.Select(attrs={"class": FORM_CONTROL}),
            "descripcion": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "fecha_emision": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "fecha_vencimiento": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "archivo": forms.ClearableFileInput(attrs={"class": FORM_CONTROL}),
        }


class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        fields = [
            "vehiculo",
            "taller",
            "fecha_programada",
            "fecha_real",
            "km_programado",
            "km_real",
            "tipo",
            "descripcion",
            "costo_mano_obra",
            "estado",
        ]
        widgets = {
            "vehiculo": forms.Select(attrs={"class": FORM_CONTROL}),
            "taller": forms.Select(attrs={"class": FORM_CONTROL}),
            "fecha_programada": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "fecha_real": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "km_programado": forms.NumberInput(attrs={"class": FORM_CONTROL}),
            "km_real": forms.NumberInput(attrs={"class": FORM_CONTROL}),
            "tipo": forms.Select(attrs={"class": FORM_CONTROL}),
            "descripcion": forms.Textarea(
                attrs={"class": FORM_CONTROL, "rows": 3}
            ),
            "costo_mano_obra": forms.NumberInput(
                attrs={"class": FORM_CONTROL, "step": "0.01"}
            ),
            "estado": forms.Select(attrs={"class": FORM_CONTROL}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["vehiculo"].queryset = Vehiculo.objects.filter(activo=True).order_by("patente")
        self.fields["taller"].queryset = Taller.objects.filter(activo=True).order_by("nombre")

        self.fields["descripcion"].required = False
        self.fields["fecha_real"].required = False
        self.fields["km_programado"].required = False
        self.fields["km_real"].required = False
        self.fields["costo_mano_obra"].required = False

    def clean(self):
        cleaned_data = super().clean()
        fecha_programada = cleaned_data.get("fecha_programada")
        fecha_real = cleaned_data.get("fecha_real")
        km_programado = cleaned_data.get("km_programado")
        km_real = cleaned_data.get("km_real")

        if fecha_programada and fecha_real and fecha_real < fecha_programada:
            self.add_error(
                "fecha_real",
                "La fecha real no puede ser menor que la fecha programada."
            )

        if km_programado and km_real and km_real < km_programado:
            self.add_error(
                "km_real",
                "El kilometraje real no puede ser menor que el programado."
            )

        return cleaned_data


class RepuestoMantenimientoForm(forms.ModelForm):
    class Meta:
        model = RepuestoMantenimiento
        fields = ["producto", "bodega", "cantidad"]
        widgets = {
            "producto": forms.Select(attrs={"class": FORM_CONTROL}),
            "bodega": forms.Select(attrs={"class": FORM_CONTROL}),
            "cantidad": forms.NumberInput(
                attrs={"class": FORM_CONTROL, "step": "0.01", "min": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Producto = apps.get_model("inventario", "Producto")
        Bodega = apps.get_model("inventario", "Bodega")

        self.fields["producto"].queryset = Producto.objects.all().order_by("nombre")
        self.fields["bodega"].queryset = Bodega.objects.all().order_by("nombre")

    def clean_cantidad(self):
        cantidad = self.cleaned_data["cantidad"]
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return cantidad


class MultaConductorForm(forms.ModelForm):
    class Meta:
        model = MultaConductor
        fields = "__all__"
        widgets = {
            "conductor": forms.Select(attrs={"class": FORM_CONTROL}),
            "vehiculo": forms.Select(attrs={"class": FORM_CONTROL}),
            "fecha": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "infraccion": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "monto": forms.NumberInput(
                attrs={"class": FORM_CONTROL, "step": "0.01"}
            ),
            "estado": forms.Select(attrs={"class": FORM_CONTROL}),
            "observaciones": forms.Textarea(
                attrs={"class": FORM_CONTROL, "rows": 3}
            ),
        }


# Compatibilidad temporal
class RutaViajeForm(forms.ModelForm):
    class Meta:
        model = RutaViaje
        fields = "__all__"
        widgets = {
            "nombre": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "origen": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "destino": forms.TextInput(attrs={"class": FORM_CONTROL}),
            "distancia_km": forms.NumberInput(
                attrs={"class": FORM_CONTROL, "step": "0.01"}
            ),
            "duracion_estimada": forms.TextInput(
                attrs={
                    "class": FORM_CONTROL,
                    "placeholder": "HH:MM:SS",
                }
            ),
            "peajes_aprox": forms.NumberInput(
                attrs={"class": FORM_CONTROL, "step": "0.01"}
            ),
            "observaciones": forms.Textarea(
                attrs={"class": FORM_CONTROL, "rows": 3}
            ),
            "activo": forms.CheckboxInput(attrs={"class": FORM_CHECK}),
        }


# Compatibilidad temporal
class CoordinacionViajeForm(forms.ModelForm):
    class Meta:
        model = CoordinacionViaje
        fields = [
            "fecha_carga",
            "fecha_descarga",
            "sobreestadia_dias",
            "estado",
            "ruta",
            "origen",
            "destino",
            "conductor",
            "tracto_camion",
            "semirremolque",
            "observaciones",
        ]
        widgets = {
            "fecha_carga": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "fecha_descarga": forms.DateInput(
                attrs={"class": FORM_CONTROL, "type": "date"}
            ),
            "sobreestadia_dias": forms.NumberInput(
                attrs={"class": FORM_CONTROL, "min": "0"}
            ),
            "estado": forms.Select(attrs={"class": FORM_CONTROL}),
            "ruta": forms.Select(attrs={"class": FORM_CONTROL}),
            "origen": forms.TextInput(
                attrs={"class": FORM_CONTROL, "readonly": "readonly"}
            ),
            "destino": forms.TextInput(
                attrs={"class": FORM_CONTROL, "readonly": "readonly"}
            ),
            "conductor": forms.Select(attrs={"class": FORM_CONTROL}),
            "tracto_camion": forms.Select(attrs={"class": FORM_CONTROL}),
            "semirremolque": forms.Select(attrs={"class": FORM_CONTROL}),
            "observaciones": forms.Textarea(
                attrs={"class": FORM_CONTROL, "rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tracto_camion"].queryset = Vehiculo.objects.filter(
            tipo="TRACTO",
            activo=True
        ).order_by("patente")

        self.fields["semirremolque"].queryset = Vehiculo.objects.filter(
            tipo="SEMIRREMOLQUE",
            activo=True
        ).order_by("patente")