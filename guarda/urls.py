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

from .new_views import (
    dashboard,
    frequencia,
    listaGuarda,
    cadastroEvento,
    eventos,
    relatorio,
    admin,
    cadastroGuarda,
    mirim_home,
    delete_object,
)

app_name = "guarda"

new_urlpatterns = [
    path("home/", home, name="home"),
    path("mirim/home/", mirim_home, name="mirim_home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("frequencia/", frequencia, name="frequencia"),
    path("guardas/", listaGuarda, name="guardas"),
    path("cadastro-evento/", cadastroEvento, name="cadastro_evento"),
    path("eventos/", eventos, name="eventos"),
    path("relatorio/", relatorio, name="relatorio"),
    path("admin/", admin, name="admin"),
    path("cadastro-guarda/", cadastroGuarda, name="cadastro_guarda"),
    path("delete-object/", delete_object, name="delete_object"),
]


urlpatterns = [
    path("", home, name="home"),
    path("createguarda/", createguarda, name="createguarda"),
    path("updateguarda/<int:guarda_pk>/", createguarda, name="updateguarda"),
    path("readguarda/", readguarda, name="readguarda"),
    path("passwordguarda/<int:guarda_pk>/", passwordguarda, name="passwordguarda"),
    path("permissoes/<int:guarda_pk>/", permissoes, name="permissoes"),
    path("importaguardas/", importaguardas, name="importaguardas"),
    path("relatorio/geral", relatorio_geral, name="relatorio_geral"),
    path("relatorio/entregas/", relatorio_entregas, name="relatorio_entregas"),
    path("relatorio/por-equipe/", relatorio_por_equipe, name="relatorio_por_equipe"),
    path("reconhecimento/", reconhecimento_facial, name="reconhecimento_facial"),
]

urlpatterns.extend(new_urlpatterns)
