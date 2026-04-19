from django import forms
from .models import GastoCombustible, GastoPeaje, CostoViaje
from taller.models import Vehiculo, Conductor
from operaciones.models import EstatusOperacionalViaje

class GastoCombustibleForm(forms.ModelForm):
    precio_litro = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        label="Precio por litro ($)",
        help_text="Ingresa el precio por litro para calcular el monto"
    )
    
    class Meta:
        model = GastoCombustible
        fields = ['vehiculo', 'conductor', 'viaje', 'fecha', 'litros', 'precio_litro', 'monto', 'kilometraje', 'observacion']
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-control', 'id': 'id_vehiculo'}),
            'conductor': forms.Select(attrs={'class': 'form-control'}),
            'viaje': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'litros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_litros'}),
            'precio_litro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_precio_litro'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly', 'id': 'id_monto'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_kilometraje'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(activo=True).order_by('patente')
        self.fields['conductor'].queryset = Conductor.objects.filter(activo=True).order_by('apellidos')
        self.fields['viaje'].queryset = EstatusOperacionalViaje.objects.all().order_by('-fecha')
        self.fields['monto'].required = False
        self.fields['precio_litro'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        litros = cleaned_data.get('litros')
        precio_litro = cleaned_data.get('precio_litro')
        monto = cleaned_data.get('monto')
        
        if litros and precio_litro and not monto:
            cleaned_data['monto'] = litros * precio_litro
        elif litros and monto and not precio_litro:
            cleaned_data['precio_litro'] = monto / litros if litros > 0 else 0
        
        return cleaned_data


class GastoPeajeForm(forms.ModelForm):
    class Meta:
        model = GastoPeaje
        fields = ['vehiculo', 'conductor', 'viaje', 'fecha', 'ruta', 'monto', 'observacion']
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'conductor': forms.Select(attrs={'class': 'form-control'}),
            'viaje': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ruta': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(activo=True).order_by('patente')
        self.fields['conductor'].queryset = Conductor.objects.filter(activo=True).order_by('apellidos')
        self.fields['viaje'].queryset = EstatusOperacionalViaje.objects.all().order_by('-fecha')


class CostoViajeForm(forms.ModelForm):
    class Meta:
        model = CostoViaje
        fields = ['viaje', 'vehiculo', 'conductor', 'km_recorridos', 'total_combustible', 'total_peajes', 'total_mantencion', 'fecha']
        widgets = {
            'viaje': forms.Select(attrs={'class': 'form-control'}),
            'vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'conductor': forms.Select(attrs={'class': 'form-control'}),
            'km_recorridos': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_combustible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_peajes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_mantencion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }