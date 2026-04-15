# signals.py
import face_recognition
import numpy as np
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Guarda

@receiver(post_save, sender=Guarda)
def atualizar_encoding(sender, instance, **kwargs):
    """
    Gera o encoding facial automaticamente quando a foto é criada ou alterada.
    """
    if instance.foto:
        try:
            imagem = face_recognition.load_image_file(instance.foto.path)
            rostos = face_recognition.face_encodings(imagem)
            if rostos:
                encoding = np.array(rostos[0]).astype(np.float32)
                instance.encoding = encoding.tobytes()
                Guarda.objects.filter(pk=instance.pk).update(encoding=instance.encoding)
        except Exception as e:
            print(f"Erro ao gerar encoding para {instance.nome}: {e}")
