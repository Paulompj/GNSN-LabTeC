from django.forms import ModelForm
from .models import Camisa
from django import forms


class CamisaForm(ModelForm):
    class Meta:
        model = Camisa
        fields = [
            "ano",
            "equipe",
            "situacao",
            "tamcamisa",
            "recebido",
            "arquivo",
            "recebedor",
            "entregador",
            "data",
        ]
        widgets = {
            "ano": forms.NumberInput(attrs={"class": "form-control"}),
            "equipe": forms.TextInput(attrs={"class": "form-control"}),
            "situacao": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "tamcamisa": forms.Select(attrs={"class": "form-control"}),
            "recebido": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "arquivo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control-file",
                    "accept": "image/*,application/pdf",
                }
            ),
            "recebedor": forms.TextInput(attrs={"class": "form-control"}),
            "entregador": forms.Select(attrs={"class": "form-control"}),
            "data": forms.TextInput(
                attrs={"data-mask": "DD/MM/AAAA", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos controlados pela view
        self.fields["entregador"].required = False
        self.fields["data"].required = False
        self.fields["situacao"].required = False
        self.fields["recebido"].required = False
