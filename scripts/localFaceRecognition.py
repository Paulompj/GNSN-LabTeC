import os
import django
import requests
import numpy as np
import face_recognition
from io import BytesIO

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GNSN.settings')
django.setup()

from app.models import Guarda

def gerar_encoding_imagem(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        image = face_recognition.load_image_file(BytesIO(response.content))
        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 0:
            print(f"❌ Nenhum rosto detectado em {url}")
            return None

        encoding = np.array(encodings[0], dtype=np.float32)
        return encoding.tobytes()

    except Exception as e:
        print(f"⚠️ Erro ao processar {url}: {e}")
        return None


def atualizar_guardas():
    #guardas = Guarda.objects.all()
    guardas = Guarda.objects.filter(matricula__in=[772, 885, 892, 1119, 1122, 1224, 1238, 1430, 1561, 1588, 1762, 1766, 1791, 1848, 2021, 2042, 2066, 2103, 2104, 2108, 2127, 2202, 2358, 2395, 2439, 2446, 2485, 2535, 2632, 2654, 2666, 2751, 2773, 2802, 2808, 2813, 3166, 3206, 3279, 3283, 3293, 3299, 3309, 3314, 3319, 3385, 3392, 3437, 3450, 3482, 3495, 3521, 3531, 3538, 3588, 3591, 3593, 3595, 3598, 3617, 3631, 3632, 3675, 3687, 3710, 3718, 3721, 3839, 3960, 4156])
    total = guardas.count()
    atualizados = 0

    for guarda in guardas:
        if not getattr(guarda, 'foto', None):
            print(f"⚠️ Guarda {guarda.pk} sem foto — ignorado.")
            continue

        url = str(guarda.foto)
        if not url.startswith("http"):
            print(f"⚠️ URL inválida para guarda {guarda.pk}: {url}")
            continue

        encoding_bytes = gerar_encoding_imagem(url)
        if encoding_bytes:
            guarda.encoding = encoding_bytes
            guarda.save(update_fields=['encoding'])
            atualizados += 1
            print(f"✅ Encoding atualizado para guarda {guarda.pk}")

    print(f"\nFinalizado. {atualizados}/{total} guardas atualizados com sucesso.")


if __name__ == "__main__":
    atualizar_guardas()
