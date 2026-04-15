from django.urls import path
from . import views

app_name = "mirim"

urlpatterns = [
    path('', views.home, name='home'),
    path("dashboard", views.dashboard, name="dashboard"),

    # Categorias
    path("categorias/", views.categoria_list, name="categoria_list"),
    path("categorias/nova/", views.categoria_create, name="categoria_create"),

    # Locais
    path("locais/", views.local_list, name="local_list"),
    path("locais/novo/", views.local_create, name="local_create"),

    # Guardas
    path("guardas/", views.guarda_list, name="guarda_list"),
    path("guardas/novo/", views.guarda_create, name="guarda_create"),
    path("guardas/<int:pk>/", views.guarda_detail, name="guarda_detail"),

    # Eventos
    path("eventos/", views.evento_list, name="evento_list"),
    path("eventos/novo/", views.evento_create, name="evento_create"),

    # Frequência
    path("frequencia/nova/", views.frequencia_create, name="frequencia_create"),
    path("eventos/<int:evento_id>/checkin/", views.checkin_evento, name="checkin_evento"),
    path("categorias/<int:pk>/editar/", views.categoria_update, name="categoria_update"),
    path("locais/<int:pk>/editar/", views.local_update, name="local_update"),
    path("guardas/<int:pk>/editar/", views.guarda_update, name="guarda_update"),
    path("eventos/<int:pk>/editar/", views.evento_update, name="evento_update"),
    path('guarda/<int:pk>/consulta/', views.guarda_consulta, name='guarda_consulta'),

    path('cirios/', views.cirio_list, name='cirio_list'),
    path('cirios/novo/', views.cirio_form, name='cirio_create'),
    path('cirios/<int:pk>/', views.cirio_detail, name='cirio_detail'),
    path('cirios/<int:pk>/editar/', views.cirio_form, name='cirio_update'),
    path('cirios/<int:pk>/excluir/', views.cirio_delete, name='cirio_delete'),

    # DELETE GENÉRICO
    path("delete/", views.delete_object, name="delete_object"),
    path("consulta/", views.mirim_consulta, name="consulta"),
    path("me/", views.mirim_detail_consulta, name="mirim_detail_logado"),
]
