from django.contrib import admin
from .models import (
    CategoriaEvento,
    Local,
    Evento,
    Frequencia,
    Cirio,
    RegraCirio,
)

# ---------- Categoria ----------
@admin.register(CategoriaEvento)
class CategoriaEventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome",)
    ordering = ("nome",)

# ---------- Local ----------
@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome",)
    ordering = ("nome",)

# ---------- Evento ----------
class FrequenciaEventoInline(admin.TabularInline):
    model = Frequencia
    extra = 0
    autocomplete_fields = () # Removido para evitar erro de ModelAdmin faltante do Guarda
    readonly_fields = ("data_registro",)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("categoria", "local", "data", "hora", "criado_em")
    list_filter = ("categoria", "local", "data")
    search_fields = ("categoria__nome", "local__nome")
    readonly_fields = ("criado_em",)
    inlines = [FrequenciaEventoInline]
    ordering = ("-data", "-hora")
    date_hierarchy = "data"

# ---------- Frequência ----------
@admin.register(Frequencia)
class FrequenciaAdmin(admin.ModelAdmin):
    list_display = (
        "guarda",
        "evento",
        "registrado_por_reconhecimento_facial",
        "data_registro",
    )
    list_filter = (
        "registrado_por_reconhecimento_facial",
        "evento__categoria",
        "evento__local",
        "evento__data",
    )
    search_fields = (
        "guarda__pessoa__nome",
        "guarda__matricula",
    )
    autocomplete_fields = ("evento",) # Removido "guarda" para evitar erro de autocomplete s/ admin
    readonly_fields = ("data_registro",)
    ordering = ("-data_registro",)

# ---------- Regras Inline ----------
class RegraCirioInline(admin.TabularInline):
    model = RegraCirio
    extra = 1
    autocomplete_fields = ("categoria",)

# ---------- Círio ----------
@admin.register(Cirio)
class CirioAdmin(admin.ModelAdmin):
    list_display = ("ano", "inicio", "termino", "ativo")
    list_filter = ("ativo", "ano")
    search_fields = ("ano",)
    ordering = ("-ano",)
    inlines = [RegraCirioInline]
    date_hierarchy = "inicio"

# ---------- Regra do Círio ----------
@admin.register(RegraCirio)
class RegraCirioAdmin(admin.ModelAdmin):
    list_display = ("cirio", "categoria", "quantidade_necessaria")
    list_filter = ("cirio", "categoria")
    search_fields = ("cirio__ano", "categoria__nome")
    autocomplete_fields = ("cirio", "categoria")
    ordering = ("cirio", "categoria")
