from django import forms
from .models import Factura, DetalleFactura
from operaciones.models import Viaje

class FacturaForm(forms.ModelForm):
    viajes = forms.ModelMultipleChoiceField(
        queryset=Viaje.objects.filter(facturado=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Viajes a facturar"
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
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si hay un cliente seleccionado, autocompletar sus datos
        if self.instance and self.instance.cliente_id:
            cliente = self.instance.cliente
            self.fields['razon_social_cliente'].initial = cliente.razon_social
            self.fields['rut_cliente'].initial = cliente.rut
            self.fields['giro_cliente'].initial = cliente.giro
            self.fields['direccion_cliente'].initial = cliente.direccion
            self.fields['comuna_cliente'].initial = cliente.comuna
            self.fields['ciudad_cliente'].initial = cliente.ciudad
    
    def save(self, commit=True):
        factura = super().save(commit=False)
        if commit:
            factura.save()
            self.save_m2m()  # guarda ManyToMany (viajes)
            # Aquí podrías generar los detalles automáticamente desde los viajes seleccionados
            for viaje in self.cleaned_data['viajes']:
                DetalleFactura.objects.create(
                    factura=factura,
                    descripcion=f"Servicio de transporte {viaje.origen} → {viaje.destino}",
                    cantidad=1,
                    unidad="VIAJE",
                    precio_unitario=viaje.monto  # asumiendo que Viaje tiene campo monto
                )
            factura.calcular_totales()
        return factura