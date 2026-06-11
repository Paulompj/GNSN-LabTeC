from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import Group
from usuario.models import Usuario


class GuardaForm(forms.Form):
    nome = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    matricula = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    turma = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    matricula_padrinho = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    foto = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}))
    nascimento = forms.DateField(required=False, widget=forms.TextInput(attrs={"data-mask": "DD/MM/AAAA", "class": "form-control"}))
    endereco = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    cidade = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    bairro = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    cep = forms.CharField(required=False, max_length=10, widget=forms.TextInput(attrs={"data-mask": "00000-000", "class": "form-control"}))
    cpf = forms.CharField(required=False, max_length=14, widget=forms.TextInput(attrs={"data-mask": "000.000.000-00", "class": "form-control"}))
    rg = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    sexo = forms.ChoiceField(required=False, choices=[("M", "Masculino"), ("F", "Feminino")], widget=forms.Select(attrs={"class": "form-control"}))
    estado_civil = forms.ChoiceField(required=False, choices=[("solteiro", "Solteiro(a)"), ("casado", "Casado(a)"), ("separado", "Separado(a)"), ("divorciado", "Divorciado(a)"), ("viuvo", "Viúvo(a)"), ("uniao_estavel", "União Estável")], widget=forms.Select(attrs={"class": "form-control"}))
    telefone = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    celular = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    tel_comercial = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    complemento = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    observacao = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
    UF = forms.CharField(required=False, max_length=2, widget=forms.TextInput(attrs={"class": "form-control", "maxlength": 2}))
    is_active = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    is_staff = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se for edição (já tem PK no banco)
        if self.instance and self.instance.pk:
            self.fields["matricula"].widget.attrs["disabled"] = "disabled"


class UsuarioGroupForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.exclude(name="super"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Permissões (Grupos)",
    )

    class Meta:
        model = Usuario
        fields = ["groups"]
