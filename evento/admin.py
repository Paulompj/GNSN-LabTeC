from django.contrib import admin

from .models import CategoriaEvento, Local


@admin.register(CategoriaEvento)
class CategoriaEventoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "is_ativo", "criado_em", "atualizado_em")
    list_filter = ("is_ativo",)
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "is_ativo", "criado_em", "atualizado_em")
    list_filter = ("is_ativo",)
    search_fields = ("nome",)
    ordering = ("nome",)
