# taller/forms.py

from django import forms

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
)


# --------------------------------------------------------------------
# VEHÍCULOS
# --------------------------------------------------------------------
class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        # Incluimos todos los campos del modelo; si más adelante agregas uno,
        # el form seguirá funcionando sin tocar nada.
        fields = "__all__"

        widgets = {
            "patente": forms.TextInput(attrs={"class": "form-control"}),
            "marca": forms.TextInput(attrs={"class": "form-control"}),
            "modelo": forms.TextInput(attrs={"class": "form-control"}),
            "anio": forms.NumberInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "km_actual": forms.NumberInput(attrs={"class": "form-control"}),

            "nro_motor": forms.TextInput(attrs={"class": "form-control"}),
            "nro_chasis": forms.TextInput(attrs={"class": "form-control"}),
            "capacidad": forms.TextInput(attrs={"class": "form-control"}),

            "fecha_compra": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "aseguradora": forms.TextInput(attrs={"class": "form-control"}),

            # Campos adicionales de equipo (si existen en tu modelo)
            "descripcion_equipo": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "estado_equipo": forms.Select(
                attrs={"class": "form-control"}
            ),
            "tipo_remolque": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "estado": forms.Select(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# --------------------------------------------------------------------
# CONDUCTORES
# --------------------------------------------------------------------
class ConductorForm(forms.ModelForm):
    """
    ESTE es el formulario que faltaba y que tus vistas están tratando de importar.
    """

    class Meta:
        model = Conductor
        fields = "__all__"

        widgets = {
            "rut": forms.TextInput(attrs={"class": "form-control"}),
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),

            "fecha_ingreso": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "licencia_clase": forms.TextInput(attrs={"class": "form-control"}),
            "licencia_vencimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# --------------------------------------------------------------------
# REMOLQUES / SEMIRREMOLQUES
# --------------------------------------------------------------------
class RemolqueForm(forms.ModelForm):
    class Meta:
        model = Remolque
        fields = "__all__"

        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "patente": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# --------------------------------------------------------------------
# TALLERES
# --------------------------------------------------------------------
class TallerForm(forms.ModelForm):
    class Meta:
        model = Taller
        fields = "__all__"

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "ubicacion": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# --------------------------------------------------------------------
# DOCUMENTOS DE VEHÍCULOS
# --------------------------------------------------------------------
class DocumentoVehiculoForm(forms.ModelForm):
    class Meta:
        model = DocumentoVehiculo
        fields = "__all__"

        widgets = {
            "vehiculo": forms.Select(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_emision": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "fecha_vencimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "archivo": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }


# --------------------------------------------------------------------
# DOCUMENTOS DE CONDUCTORES
# --------------------------------------------------------------------
class DocumentoConductorForm(forms.ModelForm):
    class Meta:
        model = DocumentoConductor
        fields = "__all__"

        widgets = {
            "conductor": forms.Select(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_emision": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "fecha_vencimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "archivo": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }


# --------------------------------------------------------------------
# MANTENIMIENTOS
# --------------------------------------------------------------------
class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        # Para no pelear con nombres de campos, usamos todos.
        fields = "__all__"

        widgets = {
            "vehiculo": forms.Select(attrs={"class": "form-control"}),
            "taller": forms.Select(attrs={"class": "form-control"}),
            "fecha_programada": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "fecha_real": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "km_programado": forms.NumberInput(attrs={"class": "form-control"}),
            "km_real": forms.NumberInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "costo_mano_obra": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "costo_repuestos": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }


# --------------------------------------------------------------------
# MULTAS
# --------------------------------------------------------------------
class MultaConductorForm(forms.ModelForm):
    class Meta:
        model = MultaConductor
        fields = "__all__"

        widgets = {
            "conductor": forms.Select(attrs={"class": "form-control"}),
            "vehiculo": forms.Select(attrs={"class": "form-control"}),
            "fecha": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "infraccion": forms.TextInput(attrs={"class": "form-control"}),
            "monto": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "estado": forms.Select(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


# --------------------------------------------------------------------
# RUTAS DE VIAJE
# --------------------------------------------------------------------
class RutaViajeForm(forms.ModelForm):
    class Meta:
        model = RutaViaje
        fields = "__all__"

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "origen": forms.TextInput(attrs={"class": "form-control"}),
            "destino": forms.TextInput(attrs={"class": "form-control"}),
            "distancia_km": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "duracion_estimada": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "HH:MM:SS",
                }
            ),
            "peajes_aprox": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "observaciones": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# --------------------------------------------------------------------
# COORDINACIÓN DE VIAJES
# --------------------------------------------------------------------
# forms.py - Versión mejorada con ayuda contextual
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
            'fecha_carga': forms.DateInput(
                attrs={
                    'class': 'form-control datetimepicker-input',
                    'type': 'text',
                    'placeholder': 'dd/mm/aaaa',
                    'data-target': '#fecha_carga_picker'
                }
            ),
            'fecha_descarga': forms.DateInput(
                attrs={
                    'class': 'form-control datetimepicker-input',
                    'type': 'text',
                    'placeholder': 'dd/mm/aaaa',
                    'data-target': '#fecha_descarga_picker'
                }
            ),
            'sobreestadia_dias': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'ruta': forms.Select(attrs={'class': 'form-control'}),
            'origen': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'destino': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'conductor': forms.Select(attrs={'class': 'form-control'}),
            'tracto_camion': forms.Select(attrs={'class': 'form-control'}),
            'semirremolque': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtros para vehículos (mantener igual)
        self.fields["tracto_camion"].queryset = Vehiculo.objects.filter(
            tipo="TRACTO",
            activo=True
        ).order_by("patente")
        
        self.fields["semirremolque"].queryset = Vehiculo.objects.filter(
            tipo="SEMIRREMOLQUE",
            activo=True
        ).order_by("patente")