import os
import sys
import django
from django.utils import timezone

# Adiciona a raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Inicializa Django (substitua pelo nome da pasta do seu projeto, onde está settings.py)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GNSN.settings")
django.setup()

# Aqui importa os models diretamente pelo app real
# Substitua "seu_app" pelo nome do seu app onde estão os models
from app.models import Camisa, CamisaLog, Guarda


def main():
    try:
        autorizador = Guarda.objects.get(matricula=2268)
        usuario_alterador = Guarda.objects.get(matricula=3844)
    except Guarda.DoesNotExist as e:
        print(f"❌ Erro: {e}")
        return

    camisas_inaptas = Camisa.objects.filter(situacao=False)
    total = camisas_inaptas.count()

    if total == 0:
        print("⚠️ Nenhuma camisa inapta encontrada.")
        return

    print(f"🔎 Encontradas {total} camisas inaptas. Iniciando atualização...\n")

    for camisa in camisas_inaptas:
        CamisaLog.objects.create(
            camisa=camisa,
            usuario=usuario_alterador,
            tamanho_antigo=camisa.tamcamisa,
            tamanho_novo=camisa.tamcamisa,
            situacao_antiga="INAPTO",
            situacao_nova="APTO",
            equipe_antiga=camisa.equipe,
            equipe_nova=camisa.equipe,
            justificativa="APTO após o Círio",
            observacao="Autorizado por 2268 - LUIZ CARLOS DE ALMEIDA JUNIOR",
            data_alteracao=timezone.now(),
        )
        camisa.situacao = True
        camisa.save(update_fields=["situacao"])

    print(f"✅ Atualização concluída com sucesso! {total} registros alterados.")
    print("📘 Logs salvos em CamisaLog com justificativa e observação padrão.")


if __name__ == "__main__":
    main()
