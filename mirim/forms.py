from django import forms
from .models import (CategoriaEvento, Local, GuardaMirim, Evento, Frequencia, Cirio, RegraCirio)
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
class GuardaMirimForm(BootstrapModelForm):
    class Meta:
        model = GuardaMirim
        fields = [
            "nome",
            "email",
            "endereco",
            "cpf",
            "matricula",
            "foto",
            "responsavel_nome",
            "responsavel_contato",
            "parentesco_responsavel",
            "data_nascimento",
            "tamanho_camisa",
            "autismo_tdah_alergia",
            "intolerancia_alimentar",
            "doenca_cronica",
            "uso_medicamento_controlado",
            "observacoes_pais",
            "ativo",
        ]

        widgets = {
            "endereco": forms.Textarea(attrs={"rows": 3}),
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "observacoes_pais": forms.Textarea(attrs={"rows": 2}),
        }


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

