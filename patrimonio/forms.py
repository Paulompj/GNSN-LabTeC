from django import forms
from .models import Setor, Categoria, Material, Estoque, Emprestimo

class SetorForm(forms.ModelForm):
    class Meta:
        model = Setor
        fields = ["nome", "localizacao", "observacoes", "ativo"]

        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "localizacao": forms.TextInput(attrs={"class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome", "descricao"]

        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            "nome",
            "descricao",
            "categoria",
            "numero_patrimonio",
            "status",
            "setor",
        ]

        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "numero_patrimonio": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "setor": forms.Select(attrs={"class": "form-select"}),
        }

class EstoqueForm(forms.ModelForm):
    class Meta:
        model = Estoque
        fields = ["material", "quantidade", "validade", "local_provisorio"]

        widgets = {
            "material": forms.Select(attrs={"class": "form-select"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control"}),
            "validade": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "local_provisorio": forms.TextInput(attrs={"class": "form-control"}),
        }

class EmprestimoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo
        fields = ["material", "quantidade", "solicitante", "retirante", "observacoes"]

        widgets = {
            "material": forms.Select(attrs={"class": "form-select select2"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control"}),
            "solicitante": forms.Select(attrs={"class": "form-select select2"}),
            "retirante": forms.Select(attrs={"class": "form-select select2"}),

            "observacoes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Observações adicionais..."
            }),
        }