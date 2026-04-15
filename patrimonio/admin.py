from django.contrib import admin
from .models import Categoria, Setor, Material, Estoque, Emprestimo


admin.site.register(Categoria)
admin.site.register(Setor)
admin.site.register(Material)
admin.site.register(Estoque)
admin.site.register(Emprestimo)