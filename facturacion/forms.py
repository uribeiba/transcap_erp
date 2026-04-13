# facturacion/forms.py
from django import forms
from .models import Factura, DetalleFactura
from bitacora.models import Bitacora   # ← Importamos Bitacora, no Viaje

class FacturaForm(forms.ModelForm):
    viajes = forms.ModelMultipleChoiceField(
        queryset=Bitacora.objects.filter(facturado=False),  # ← Filtra servicios no facturados
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Servicios a facturar"   # ← Texto más claro
    )
    
    class Meta:
        model = Factura
        fields = ['tipo_dte', 'fecha_emision', 'fecha_vencimiento', 'cliente',
                  'razon_social_cliente', 'rut_cliente', 'giro_cliente',
                  'direccion_cliente', 'comuna_cliente', 'ciudad_cliente',
                  'observaciones', 'viajes']
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'cliente': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Seleccione un cliente...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar clientes
        self.fields['cliente'].queryset = self.fields['cliente'].queryset.order_by('razon_social')
        
        # Forzar formato ISO en fechas (evita warning en consola)
        if self.instance and self.instance.pk:
            if self.instance.fecha_emision:
                self.initial['fecha_emision'] = self.instance.fecha_emision.isoformat()
            if self.instance.fecha_vencimiento:
                self.initial['fecha_vencimiento'] = self.instance.fecha_vencimiento.isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        viajes = cleaned_data.get('viajes')
        if not viajes:
            raise forms.ValidationError("Debe seleccionar al menos un servicio para facturar.")
        return cleaned_data
    
    def save(self, commit=True):
        factura = super().save(commit=False)
        if commit:
            factura.save()
            self.save_m2m()  # guarda la relación ManyToMany (servicios)
            
            # Crear detalles de factura a partir de los servicios seleccionados
            for bitacora in self.cleaned_data['viajes']:
                DetalleFactura.objects.create(
                    factura=factura,
                    descripcion=f"Servicio de transporte {bitacora.origen} → {bitacora.destino}",
                    cantidad=1,
                    unidad="VIAJE",
                    precio_unitario=bitacora.tarifa_flete   # ← Usa el monto del servicio
                )
            factura.calcular_totales()
        return factura