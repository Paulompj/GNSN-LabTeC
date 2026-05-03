from django.urls import path

from .views import (
    home,
    createguarda,
    readguarda,
    passwordguarda,
    permissoes,
    importaguardas,
    relatorio_geral,
    relatorio_entregas,
    relatorio_por_equipe,
    reconhecimento_facial,
)

app_name = "guarda"

urlpatterns = [
    path("", home, name="home"),
    path("createguarda/", createguarda, name="createguarda"),
    path("updateguarda/<int:idguarda>/", createguarda, name="updateguarda"),
    path("readguarda/", readguarda, name="readguarda"),
    path("passwordguarda/<int:idguarda>/", passwordguarda, name="passwordguarda"),
    path("permissoes/<int:idguarda>/", permissoes, name="permissoes"),
    path("importaguardas/", importaguardas, name="importaguardas"),
    path("relatorio/geral", relatorio_geral, name="relatorio_geral"),
    path("relatorio/entregas/", relatorio_entregas, name="relatorio_entregas"),
    path("relatorio/por-equipe/", relatorio_por_equipe, name="relatorio_por_equipe"),
    path("reconhecimento/", reconhecimento_facial, name="reconhecimento_facial"),
]
