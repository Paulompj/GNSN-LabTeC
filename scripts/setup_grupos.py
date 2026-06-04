"""
Popula o banco com os grupos de permissão do sistema e atribui o grupo
'super' ao primeiro superusuário encontrado.

Uso: python setup_grupos.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GNSN.settings")
django.setup()

from django.contrib.auth.models import Group
from guarda.models import Guarda

GRUPOS = [
    "super",
    "Direção",
    "Comissão",
    "Entregador_geral",
    "Patrimonio_adm",
    "Patrimonio_solicitante",
    "Mirim_adm",
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
        Guarda.objects.filter(is_superuser=True).order_by("pk").first()
    )

    if superuser is None:
        print("  ⚠️  Nenhum superusuário encontrado. Crie um com:")
        print("       python manage.py createsuperuser")
        return

    grupo_super = Group.objects.get(name="super")
    if superuser.groups.filter(name="super").exists():
        print(f"  ⏭️  {superuser.nome} (matrícula {superuser.matricula}) já possui o grupo 'super'")
    else:
        superuser.groups.add(grupo_super)
        print(f"  ✅ Grupo 'super' atribuído a {superuser.nome} (matrícula {superuser.matricula})")


if __name__ == "__main__":
    criar_grupos()
    atribuir_super_ao_superuser()
    print("\n✔ Concluído.\n")
