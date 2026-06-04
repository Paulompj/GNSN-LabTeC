from django import forms
from .models import (CategoriaEvento, Local, Evento, Frequencia, Cirio, RegraCirio)
from guarda.models import Guarda, Pessoa, Endereco, FichaSaude, ResponsavelGuarda
from django.forms import inlineformset_factory

RegraCirioFormSet = inlineformset_factory(
    Cirio,
    RegraCirio,
    fields=("categoria", "quantidade_necessaria"),
    extra=1,
    can_delete=True
)

# ---------- Base Bootstrap ----------
class BootstrapModelForm(forms.ModelForm):
    """Aplica classes Bootstrap automaticamente."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            css_class = "form-control"

            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.FileInput):
                css_class = "form-control"

            field.widget.attrs.update({"class": css_class})


# ---------- Categoria ----------
class CategoriaEventoForm(BootstrapModelForm):
    class Meta:
        model = CategoriaEvento
        fields = ["nome", "ativo"]


# ---------- Local ----------
class LocalForm(BootstrapModelForm):
    class Meta:
        model = Local
        fields = ["nome", "ativo"]


# ---------- Guarda Mirim ----------
class GuardaMirimForm(forms.Form):
    # Pessoa
    nome = forms.CharField(max_length=200, label="Nome da Criança/Jovem")
    cpf = forms.CharField(max_length=14, required=False, label="CPF")
    data_nascimento = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    email = forms.EmailField(required=False)
    foto = forms.ImageField(required=False)
    
    # Endereço
    endereco = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Endereço Completo")

    # Guarda
    matricula = forms.CharField(max_length=7, label="Matrícula")
    ativo = forms.BooleanField(required=False, initial=True)
    tamanho_camisa = forms.CharField(max_length=10, required=False)

    # Responsável
    responsavel_nome = forms.CharField(max_length=200, label="Nome do Responsável")
    responsavel_contato = forms.CharField(max_length=20, required=False, label="Contato do Responsável")
    parentesco_responsavel = forms.CharField(max_length=50, required=False, label="Parentesco")

    # Ficha Saude
    autismo_tdah_alergia = forms.CharField(max_length=250, required=False, label="Autismo/TDAH/Alergia")
    intolerancia_alimentar = forms.CharField(max_length=250, required=False, label="Intolerância Alimentar")
    doenca_cronica = forms.CharField(max_length=250, required=False, label="Doença Crônica")
    uso_medicamento_controlado = forms.CharField(max_length=250, required=False, label="Uso de Medicamento")
    observacoes_pais = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Observações dos Pais")

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        
        # Populate initial data if instance is provided (instance is Guarda)
        if self.instance:
            p = self.instance.pessoa
            self.fields["nome"].initial = p.nome
            self.fields["cpf"].initial = p.cpf
            self.fields["data_nascimento"].initial = p.data_nascimento
            self.fields["email"].initial = p.email
            self.fields["foto"].initial = p.foto
            
            # Endereço
            if hasattr(p, "endereco_obj") and p.endereco_obj:
                self.fields["endereco"].initial = p.endereco_obj.logradouro
            
            # Guarda
            self.fields["matricula"].initial = self.instance.matricula
            self.fields["ativo"].initial = (self.instance.status == "Ativo")
            
            # Responsavel
            resp = self.instance.responsaveis.first()
            if resp:
                self.fields["responsavel_nome"].initial = resp.pessoa.nome
                self.fields["responsavel_contato"].initial = resp.pessoa.telefone
                self.fields["parentesco_responsavel"].initial = resp.parentesco
            
            # Ficha Saúde
            if hasattr(p, "fichasaude"):
                fs = p.fichasaude
                self.fields["autismo_tdah_alergia"].initial = fs.alergias
                self.fields["intolerancia_alimentar"].initial = fs.restricao_alimentar
                self.fields["doenca_cronica"].initial = fs.doenca_cronica
                self.fields["uso_medicamento_controlado"].initial = fs.medicamento_continuo
                self.fields["observacoes_pais"].initial = fs.contato_emergencia

        # Apply bootstrap
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs.update({"class": css_class})



# ---------- Evento ----------
class EventoForm(BootstrapModelForm):
    class Meta:
        model = Evento
        fields = ["categoria", "local", "data", "hora"]

        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "hora": forms.TimeInput(attrs={"type": "time"}),
        }


# ---------- Frequência ----------
class FrequenciaForm(BootstrapModelForm):
    class Meta:
        model = Frequencia
        fields = [
            "guarda",
            "evento",
            "registrado_por_reconhecimento_facial",
            "observacao",
        ]

        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 2}),
        }


# ---------- Check-in rápido por matrícula ----------
class CheckinMatriculaForm(forms.Form):
    matricula = forms.CharField(
        label="Matrícula do Guarda Mirim",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite a matrícula",
                "autofocus": True,
            }
        ),
    )

class CirioForm(BootstrapModelForm):
    class Meta:
        model = Cirio
        fields = ["ano", "inicio", "termino", "ativo"]

        widgets = {
            "inicio": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"}
            ),
            "termino": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔥 ESSENCIAL: força o formato correto ao editar
        for field in ["inicio", "termino"]:
            if self.instance and getattr(self.instance, field):
                self.fields[field].initial = getattr(self.instance, field).strftime("%Y-%m-%d")

class RegraCirioForm(forms.ModelForm):
    class Meta:
        model = RegraCirio
        fields = ["categoria", "quantidade_necessaria"]

