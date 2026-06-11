"""
Popula o banco com os grupos de permissão do sistema e atribui o grupo
'super' ao primeiro superusuário encontrado.

Uso: python scripts/setup_grupos.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GNSN.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

Usuario = get_user_model()

GRUPOS = [
    "super",
    "Direção",
    "Comissão",
    "Entregador_geral",
    "Patrimonio_adm",
    "Patrimonio_solicitante",
]


def criar_grupos():
    print("\n── Criando grupos ──────────────────────────────")
    for nome in GRUPOS:
        grupo, criado = Group.objects.get_or_create(name=nome)
        status = "criado" if criado else "já existe"
        print(f"  {'✅' if criado else '⏭️ '} {nome} ({status})")


def atribuir_super_ao_superuser():
    print("\n── Atribuindo grupo 'super' ao primeiro superusuário ──")
    superuser = (
        Usuario.objects.filter(is_superuser=True).order_by("pk").first()
    )

    if superuser is None:
        print("  ⚠️  Nenhum superusuário encontrado. Crie um com:")
        print("       python manage.py createsuperuser")
        return

    nome = superuser.pessoa.nome if superuser.pessoa_id else superuser.usuario
    grupo_super = Group.objects.get(name="super")
    if superuser.groups.filter(name="super").exists():
        print(f"  ⏭️  {nome} (usuário {superuser.usuario}) já possui o grupo 'super'")
    else:
        superuser.groups.add(grupo_super)
        print(f"  ✅ Grupo 'super' atribuído a {nome} (usuário {superuser.usuario})")


if __name__ == "__main__":
    criar_grupos()
    atribuir_super_ao_superuser()
    print("\n✔ Concluído.\n")
