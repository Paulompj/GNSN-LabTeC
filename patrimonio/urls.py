from django.urls import path

from . import views

app_name = "patrimonio"

urlpatterns = [
    path('', views.home, name='home'),
    path("setores/", views.setor_list, name="setor_list"),
    path("setores/novo/", views.setor_form, name="setor_create"),
    path("setores/<int:id>/editar/", views.setor_form, name="setor_edit"),
    path("setores/<int:id>/delete/", views.setor_delete, name="setor_delete"),
    path("categorias/", views.categoria_list, name="categoria_list"),
    path("categorias/nova/", views.categoria_form, name="categoria_create"),
    path("categorias/<int:id>/editar/", views.categoria_form, name="categoria_edit"),
    path("categorias/<int:id>/delete/", views.categoria_delete, name="categoria_delete"),
    path("materiais/", views.material_list, name="material_list"),
    path("materiais/novo/", views.material_form, name="material_create"),
    path("materiais/<int:id>/editar/", views.material_form, name="material_edit"),
    path("materiais/<int:id>/delete/", views.material_delete, name="material_delete"),
    path("estoque/", views.estoque_list, name="estoque_list"),
    path("estoque/novo/", views.estoque_form, name="estoque_create"),
    path("estoque/<int:id>/editar/", views.estoque_form, name="estoque_edit"),
    path("estoque/<int:id>/delete/", views.estoque_delete, name="estoque_delete"),
    path("emprestimos/", views.emprestimo_list, name="emprestimo_list"),
    path("emprestimos/novo/", views.emprestimo_form, name="emprestimo_create"),
    path("emprestimos/<int:pk>/editar/", views.emprestimo_form, name="emprestimo_edit"),
    path("emprestimos/<int:pk>/delete/", views.emprestimo_delete, name="emprestimo_delete"),
    path("emprestimos/<int:pk>/aprovar/", views.emprestimo_aprovar, name="emprestimo_aprovar"),
    path("emprestimos/<int:pk>/devolver/", views.emprestimo_devolver, name="emprestimo_devolver"),
    path('emprestimos/<int:pk>/retirar/', views.emprestimo_retirar, name='emprestimo_retirar'),
    path('emprestimos/<int:pk>/termo/', views.emprestimo_termo, name='emprestimo_termo'),
    path("relatorios/validade/", views.relatorio_validade, name="relatorio_validade"),
    path("relatorios/emprestimos-antigos/", views.relatorio_emprestimos_antigos, name="relatorio_emprestimos_antigos"),
    path("relatorios/estoque/", views.relatorio_estoque, name="relatorio_estoque"),
]
