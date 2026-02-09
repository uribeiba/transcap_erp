# suscripciones/forms.py
from django import forms
from .models import Plan

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["nombre", "max_usuarios", "orden", "precio_mensual", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "max_usuarios": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "orden": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "precio_mensual": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CambiarPlanForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(activo=True).order_by("max_usuarios", "nombre"),
        empty_label=None,
        widget=forms.Select(attrs={"class": "form-control"})
    )