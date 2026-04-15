from django.forms import ModelForm
from django import forms
from .models import Guarda, Camisa
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class GuardaForm(ModelForm):
    class Meta:
        model = Guarda
        fields = [
            'nome', 'email', 'matricula', 'turma', 'matricula_padrinho',
            'foto', 'nascimento', 'endereco', 'cidade', 'bairro', 'cep',
            'cpf', 'rg', 'sexo', 'estado_civil', 'telefone', 'celular',
            'tel_comercial', 'complemento', 'observacao', 'UF', 'is_active', 'is_staff'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'matricula': forms.NumberInput(attrs={'class': 'form-control'}),
            'turma': forms.NumberInput(attrs={'class': 'form-control'}),
            'matricula_padrinho': forms.NumberInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'nascimento': forms.TextInput(attrs={'data-mask': 'DD/MM/AAAA', 'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'data-mask': '00000-000', 'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'data-mask': '000.000.000-00', 'class': 'form-control'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            "sexo": forms.Select(attrs={"class": "form-control"}),
            "estado_civil": forms.Select(attrs={"class": "form-control"}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'tel_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'UF': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se for edição (já tem PK no banco)
        if self.instance and self.instance.pk:
            self.fields['matricula'].widget.attrs['disabled'] = 'disabled'

class LoginForm(forms.Form):
    matricula = forms.IntegerField(label="Matrícula", widget=forms.NumberInput(attrs={'class':'form-control'}))
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class':'form-control'}))

class CamisaForm(ModelForm):
    class Meta:
        model = Camisa
        fields = ['ano', 'equipe', 'situacao', 'tamcamisa', 'recebido', 'arquivo', 'recebedor', 'entregador', 'data']
        widgets = {
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'equipe': forms.TextInput(attrs={'class': 'form-control'}),
            'situacao': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tamcamisa': forms.Select(attrs={'class': 'form-control'}),
            'recebido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': 'image/*,application/pdf'}),
            'recebedor': forms.TextInput(attrs={'class': 'form-control'}),
            'entregador': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.TextInput(attrs={'data-mask': 'DD/MM/AAAA', 'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos controlados pela view
        self.fields['entregador'].required = False
        self.fields['data'].required = False
        self.fields['situacao'].required = False
        self.fields['recebido'].required = False

# Form para selecionar grupos
class GuardaGroupForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.exclude(name='super'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Permissões (Grupos)"
    )

    class Meta:
        model = Guarda
        fields = ['groups']

User = get_user_model()

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