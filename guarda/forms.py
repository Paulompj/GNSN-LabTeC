from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import Group
from .models import Guarda


class GuardaForm(ModelForm):
    class Meta:
        model = Guarda
        fields = [
            "nome",
            "email",
            "matricula",
            "turma",
            "matricula_padrinho",
            "foto",
            "nascimento",
            "endereco",
            "cidade",
            "bairro",
            "cep",
            "cpf",
            "rg",
            "sexo",
            "estado_civil",
            "telefone",
            "celular",
            "tel_comercial",
            "complemento",
            "observacao",
            "UF",
            "is_active",
            "is_staff",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "matricula": forms.NumberInput(attrs={"class": "form-control"}),
            "turma": forms.NumberInput(attrs={"class": "form-control"}),
            "matricula_padrinho": forms.NumberInput(attrs={"class": "form-control"}),
            "foto": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "nascimento": forms.TextInput(
                attrs={"data-mask": "DD/MM/AAAA", "class": "form-control"}
            ),
            "endereco": forms.TextInput(attrs={"class": "form-control"}),
            "cidade": forms.TextInput(attrs={"class": "form-control"}),
            "bairro": forms.TextInput(attrs={"class": "form-control"}),
            "cep": forms.TextInput(
                attrs={"data-mask": "00000-000", "class": "form-control"}
            ),
            "cpf": forms.TextInput(
                attrs={"data-mask": "000.000.000-00", "class": "form-control"}
            ),
            "rg": forms.TextInput(attrs={"class": "form-control"}),
            "sexo": forms.Select(attrs={"class": "form-control"}),
            "estado_civil": forms.Select(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "celular": forms.TextInput(attrs={"class": "form-control"}),
            "tel_comercial": forms.TextInput(attrs={"class": "form-control"}),
            "complemento": forms.TextInput(attrs={"class": "form-control"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "UF": forms.TextInput(attrs={"class": "form-control", "maxlength": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se for edição (já tem PK no banco)
        if self.instance and self.instance.pk:
            self.fields["matricula"].widget.attrs["disabled"] = "disabled"


class GuardaGroupForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.exclude(name="super"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Permissões (Grupos)",
    )

    class Meta:
        model = Guarda
        fields = ["groups"]
