from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone  # 🔥 NUEVO: Importar timezone

from bitacora.models import Bitacora
from centro_comercio.models import Cliente
from .models import EDP, EDPServicio, EDPago


class EDPForm(forms.ModelForm):
    class Meta:
        model = EDP
        fields = [
            "codigo",
            "cliente",
            "fecha_inicio",
            "fecha_termino",
            "responsable",
            "glosa",
            "estado",
        ]
        widgets = {
            "codigo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Código EDP",
                    "readonly": "readonly",
                }
            ),
            "cliente": forms.Select(
                attrs={
                    "class": "form-control select2-cliente",
                }
            ),
            "fecha_inicio": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "fecha_termino": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "responsable": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Responsable del EDP",
                }
            ),
            "glosa": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observación, nota o glosa del EDP...",
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }
        labels = {
            "codigo": "Código EDP",
            "cliente": "Cliente",
            "fecha_inicio": "Fecha inicio",
            "fecha_termino": "Fecha término",
            "responsable": "Responsable",
            "glosa": "Glosa / Observaciones",
            "estado": "Estado",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cliente"].queryset = Cliente.objects.filter(activo=True).order_by("razon_social")
        self.fields["cliente"].required = False
        self.fields["codigo"].required = False

        if not self.instance.pk and not self.initial.get("codigo"):
            self.fields["codigo"].initial = ""

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_termino = cleaned_data.get("fecha_termino")

        if fecha_inicio and fecha_termino and fecha_inicio > fecha_termino:
            self.add_error("fecha_termino", "La fecha término no puede ser menor que la fecha inicio.")

        return cleaned_data


class ServiciosSelectForm(forms.Form):
    """
    Se mantiene este nombre porque views.py ya lo usa.
    Aunque el step se llama 'servicios', realmente aquí
    seleccionamos registros de Bitácora.
    """
    servicios = forms.MultipleChoiceField(
        required=False,
        label="Servicios operativos / Bitácora",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        super().__init__(*args, **kwargs)
        self.fields["servicios"].choices = choices


class EDPServicioForm(forms.ModelForm):
    class Meta:
        model = EDPServicio
        fields = ["servicio", "tarifa", "estadia"]
        widgets = {
            "servicio": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "tarifa": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0",
                }
            ),
            "estadia": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0",
                }
            ),
        }
        labels = {
            "servicio": "Bitácora",
            "tarifa": "Tarifa flete",
            "estadia": "Estadía / Sobrestadía",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["servicio"].queryset = (
            Bitacora.objects.select_related("cliente", "conductor")
            .order_by("-fecha", "-id")
        )
        self.fields["servicio"].label_from_instance = self.label_bitacora

    def label_bitacora(self, obj):
        """
        Etiqueta mejorada para mostrar en el select de bitácoras
        """
        # Datos del cliente
        cliente = obj.cliente.razon_social if obj.cliente else "Sin cliente"
        
        # Fechas
        fecha = obj.fecha.strftime("%d/%m/%Y") if obj.fecha else "--/--/----"
        
        # Origen y destino
        origen = obj.origen or "-"
        destino = obj.destino or "-"
        
        # Conductor (si existe)
        conductor = ""
        if hasattr(obj, 'conductor') and obj.conductor:
            conductor_nombre = getattr(obj.conductor, 'nombre_completo', None) or str(obj.conductor)
            conductor = f" | Conductor: {conductor_nombre}"
        
        # Guías
        guias = ""
        if hasattr(obj, 'guias_raw') and obj.guias_raw:
            guias = f" | Guías: {obj.guias_raw}"
        
        # Retornar etiqueta formateada
        return f"BIT-{obj.id} | {fecha} | {cliente} | {origen} → {destino}{conductor}{guias}"


# 🔥 CLASE EDPagoForm ACTUALIZADA - Opción 3
class EDPagoForm(forms.ModelForm):
    class Meta:
        model = EDPago
        fields = ["fecha", "medio_pago", "monto", "referencia"]
        widgets = {
            "fecha": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "medio_pago": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "monto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0",
                }
            ),
            "referencia": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "N° transferencia, comprobante o referencia",
                }
            ),
        }
        labels = {
            "fecha": "Fecha",
            "medio_pago": "Medio de pago",
            "monto": "Monto",
            "referencia": "Referencia",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🔥 Hacer todos los campos NO obligatorios
        self.fields['fecha'].required = False
        self.fields['monto'].required = False
        self.fields['medio_pago'].required = False
        self.fields['referencia'].required = False
        
        # 🔥 Establecer fecha actual por defecto si no hay valor
        if not self.instance.pk and not self.initial.get('fecha'):
            self.initial['fecha'] = timezone.now().date()
    
    def clean(self):
        """
        Validación personalizada:
        - Si hay monto pero no fecha, asignar fecha actual
        - Si no hay monto, ignorar el registro (no guardar)
        """
        cleaned_data = super().clean()
        
        monto = cleaned_data.get('monto')
        fecha = cleaned_data.get('fecha')
        
        # Si hay monto pero no fecha, asignar fecha actual
        if monto and not fecha:
            cleaned_data['fecha'] = timezone.now().date()
        
        # Si no hay monto, marcar para eliminar (no guardar registro vacío)
        if not monto or monto == 0:
            # No agregar errores, simplemente se ignorará este registro
            pass
        
        return cleaned_data


EDPServicioFormSet = inlineformset_factory(
    parent_model=EDP,
    model=EDPServicio,
    form=EDPServicioForm,
    fields=["servicio", "tarifa", "estadia"],
    extra=1,
    can_delete=True,
)


EDPPagoFormSet = inlineformset_factory(
    parent_model=EDP,
    model=EDPago,
    form=EDPagoForm,
    fields=["fecha", "medio_pago", "monto", "referencia"],
    extra=1,
    can_delete=True,
)