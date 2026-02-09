from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm

from .models import Empresa, Sucursal, RolUsuario

User = get_user_model()


# =========================
# Empresa
# =========================
class EmpresaForm(forms.ModelForm):
    """
    Form solo para datos de empresa (SIN logo).
    El logo se maneja con LogoEmpresaForm.
    """
    class Meta:
        model = Empresa
        fields = ["razon_social", "rut", "direccion"]
        widgets = {
            "razon_social": forms.TextInput(attrs={"class": "form-control"}),
            "rut": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
        }


class LogoEmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["logo"]
        widgets = {
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"})
        }


# =========================
# Sucursales
# =========================
class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ["nombre"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Matriz / Los Vilos / Santiago",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")

        if self.empresa:
            qs = Sucursal.objects.filter(empresa=self.empresa, nombre__iexact=nombre)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Ya existe una sucursal con ese nombre.")

        return nombre


# =========================
# Usuarios
# =========================
class UsuarioCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    rol = forms.ChoiceField(
        choices=RolUsuario.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields["sucursal"].queryset = Sucursal.objects.filter(empresa=empresa).order_by("nombre")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("El email es obligatorio.")

        # Recomendado: evitar duplicados
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo.")
        return email


class UsuarioEditForm(forms.ModelForm):
    rol = forms.ChoiceField(
        choices=RolUsuario.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields["sucursal"].queryset = Sucursal.objects.filter(empresa=empresa).order_by("nombre")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("El email es obligatorio.")

        # Evitar duplicado, excluyendo el propio usuario
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe otro usuario con este correo.")
        return email


class UsuarioPasswordForm(SetPasswordForm):
    """Solo hereda SetPasswordForm."""
    pass
