# from django.contrib import admin
# from django.urls import reverse_lazy
# from django.contrib.auth.forms import SetPasswordForm
# from django.contrib.auth import views as auth_views

from django.urls import path
from .views import (
    home,
    login_guarda,
    logout_guarda,
    readapoio,
    entregar_apoio,
    importar_apoio,
    relatorio_apoio,
    force_change_password,
    monitoramento,
)

app_name = "app"

urlpatterns = [
    path("", home, name="home"),
    path("login/", login_guarda, name="login"),
    path("logout/", logout_guarda, name="logout"),
    path("apoio/", readapoio, name="readapoio"),
    path("apoio/<int:apoio_id>/entregar/", entregar_apoio, name="entregarapoio"),
    path("importarapoio/", importar_apoio, name="importarapoio"),
    path("trocar-senha/", force_change_password, name="password_change"),
    path("monitoramento/", monitoramento, name="monitoramento"),
    path("relatorio_apoio", relatorio_apoio, name="relatorio_apoio"),
]
