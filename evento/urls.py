from django.urls import path

from . import views

app_name = "evento"

urlpatterns = [
    path("categorias/", views.categoria_list, name="categoria_list"),
    path("categorias/nova/", views.categoria_create, name="categoria_create"),
    path(
        "categorias/<int:pk>/editar/",
        views.categoria_update,
        name="categoria_update",
    ),
    path(
        "categorias/<int:pk>/excluir/",
        views.categoria_delete,
        name="categoria_delete",
    ),
    path("locais/", views.local_list, name="local_list"),
    path("locais/novo/", views.local_create, name="local_create"),
    path("locais/<int:pk>/editar/", views.local_update, name="local_update"),
    path("locais/<int:pk>/excluir/", views.local_delete, name="local_delete"),
]
