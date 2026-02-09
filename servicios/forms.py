from django import forms
from .models import Servicio
from centro_comercio.models import Cotizacion
from django.utils import timezone

class ServicioForm(forms.ModelForm):
    cotizacion = forms.ModelChoiceField(
        queryset=Cotizacion.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Seleccionar Cotización"
    )
    
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date', 
                'class': 'form-control',
                'placeholder': 'DD/MM/AAAA'
            }
        ),
        required=True,
        label="Inicio Servicio"
    )
    
    fecha_termino = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date', 
                'class': 'form-control',
                'placeholder': 'DD/MM/AAAA'
            }
        ),
        required=True,
        label="Término Servicio"
    )

    class Meta:
        model = Servicio
        fields = ['codigo', 'cotizacion', 'fecha_inicio', 'fecha_termino', 'descripcion', 'estado', 'notas_internas']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del servicio...'
            }),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas_internas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas internas...'
            }),
        }
        labels = {
            'codigo': 'Código Servicio',
            'descripcion': 'Descripción',
            'notas_internas': 'Notas Internas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ordenar cotizaciones por código descendente
        self.fields['cotizacion'].queryset = Cotizacion.objects.all().order_by('-codigo')
        
        # Si es un nuevo servicio, generar código automático
        if not self.instance.pk:
            self.initial['codigo'] = Servicio.siguiente_codigo()
            # Establecer fecha actual como predeterminada
            self.initial['fecha_inicio'] = timezone.localdate()
            self.initial['fecha_termino'] = timezone.localdate()

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_termino = cleaned_data.get('fecha_termino')

        if fecha_inicio and fecha_termino:
            if fecha_termino < fecha_inicio:
                self.add_error('fecha_termino', 
                    'La fecha de término no puede ser anterior a la fecha de inicio.')
        
        return cleaned_data