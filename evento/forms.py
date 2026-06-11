from django import forms

from .models import CategoriaEvento, Local


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            css_class = "form-control"

            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"

            field.widget.attrs.update({"class": css_class})


class CategoriaEventoForm(BootstrapModelForm):
    class Meta:
        model = CategoriaEvento
        fields = ["nome", "is_ativo"]
        labels = {"is_ativo": "Ativa"}


class LocalForm(BootstrapModelForm):
    class Meta:
        model = Local
        fields = ["nome", "is_ativo"]
        labels = {"is_ativo": "Ativo"}
