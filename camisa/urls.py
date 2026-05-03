from django.urls import path

from .views import (
    home,
    readcamisa,
    createcamisa,
    changecamisa,
    deletar_camisas_por_ano,
    findcamisa,
    takecamisa,
    entregar_camisa,
    relatorio_geral,
    relatorio_por_tamanho,
    relatorio_por_equipe,
    camisa_entregue,
    minhas_entregas,
    importacamisas,
)

app_name = "camisa"

urlpatterns = [
    path("", home, name="home"),
    path("readcamisa/", readcamisa, name="readcamisa"),
    path("createcamisa/<int:guarda_id>", createcamisa, name="createcamisa"),
    path("changecamisa/<int:idcamisa>/", changecamisa, name="changecamisa"),
    path("deletar/", deletar_camisas_por_ano, name="deletar_camisas_por_ano"),
    path("minhas_entregas/", minhas_entregas, name="minhas_entregas"),
    path("findcamisa/", findcamisa, name="findcamisa"),
    path("takecamisa/", takecamisa, name="takecamisa"),
    path("entregar_camisa/", entregar_camisa, name="entregar_camisa"),
    path("camisa_entregue/", camisa_entregue, name="camisa_entregue"),
    path("importacamisas/", importacamisas, name="importacamisas"),
    path("relatorio/geral", relatorio_geral, name="relatorio_geral"),
    path(
        "relatorio/por-tamanho",
        relatorio_por_tamanho,
        name="relatorio_por_tamanho",
    ),
    path(
        "relatorio/por-equipe",
        relatorio_por_equipe,
        name="relatorio_por_equipe",
    ),
]
