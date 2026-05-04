from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class LoginForm(forms.Form):
    matricula = forms.IntegerField(
        label="Matrícula", widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    senha = forms.CharField(
        label="Senha", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class ForceChangePasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean_new_password1(self):
        senha = self.cleaned_data.get("new_password1")
        try:
            validate_password(senha)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return senha

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password1") != cleaned_data.get("new_password2"):
            raise forms.ValidationError("As senhas não coincidem")
        return cleaned_data
