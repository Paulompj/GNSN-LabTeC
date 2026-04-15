from django.contrib import admin
from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import SetPasswordForm
from .views import (home, createguarda, findcamisa, takecamisa, entregar_camisa, login_guarda, logout_guarda,
                    readguarda, passwordguarda, changecamisa,readcamisa, relatorios, relatorio2, permissoes,
                    importacamisas, importaguardas, deletar_camisas_por_ano, relatorio_entregas, relatorio_camisas,
                    relatorio_barras, camisa_entregue, readapoio, entregar_apoio, importar_apoio, relatorio_apoio,
                    force_change_password, monitoramento, minhas_entregas, relatorio_camisas2, reconhecimento_facial,
                    createcamisa)

app_name = "app"

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_guarda, name='login'),
    path('logout/', logout_guarda, name='logout'),
    path('createguarda/', createguarda, name='createguarda'),
    path('createcamisa/<int:guarda_id>', createcamisa, name='createcamisa'),
    path('updateguarda/<int:idguarda>/', createguarda, name='updateguarda'),
    path('readguarda/', readguarda, name='readguarda'),
    path('passwordguarda/<int:idguarda>/', passwordguarda, name='passwordguarda'),
    path('readcamisa/', readcamisa, name='readcamisa'),
    path('changecamisa/<int:idcamisa>/', changecamisa, name='changecamisa'),
    path('findcamisa/', findcamisa, name='findcamisa'),
    path('takecamisa/', takecamisa, name='takecamisa'),
    path('entregar_camisa/', entregar_camisa, name='entregar_camisa'),
    path('relatorios/', relatorios, name='relatorios'),
    path('relatorio2/', relatorio2, name='relatorio2'),
    path('permissoes/<int:idguarda>/', permissoes, name='permissoes'),
    path("importacamisas/", importacamisas, name="importacamisas"),
    path('importaguardas/', importaguardas, name='importaguardas'),
    path('deletar/', deletar_camisas_por_ano, name='deletar_camisas_por_ano'),
    path('relatorio_entregas/', relatorio_entregas, name='relatorio_entregas'),
    path('relatorio_camisas/', relatorio_camisas, name='relatorio_camisas'),
    path('relatorio_camisas2/', relatorio_camisas2, name='relatorio_camisas2'),
    path('relatorio-barras/', relatorio_barras, name='relatorio_barras'),
    path('camisa_entregue/', camisa_entregue, name='camisa_entregue'),
    path('apoio/', readapoio, name='readapoio'),
    path('apoio/<int:apoio_id>/entregar/', entregar_apoio, name='entregarapoio'),
    path("importarapoio/",importar_apoio, name="importarapoio"),
    path('relatorio_apoio', relatorio_apoio, name='relatorio_apoio'),
    path("trocar-senha/", force_change_password, name="password_change"),
    path('monitoramento/', monitoramento, name='monitoramento'),
    path("minhas_entregas/", minhas_entregas, name="minhas_entregas"),
    path("reconhecimento/", reconhecimento_facial, name="reconhecimento_facial"),
]
