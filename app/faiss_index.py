import faiss
import numpy as np
from .models import Guarda

class FaceIndex:
    def __init__(self):
        self.index = None
        self.guardas = []
        self.load_index()

    def load_index(self):
        self.guardas = Guarda.objects.exclude(encoding=None)

        encodings = []
        valid_guardas = []

        for g in self.guardas:
            try:
                arr = np.frombuffer(g.encoding, dtype=np.float32)
                if arr.size in [128, 512]:  # tamanho esperado
                    encodings.append(arr)
                    valid_guardas.append(g)
                else:
                    print(f"⚠️ Encoding inválido para {g.matricula}: tamanho {arr.size}")
            except Exception as e:
                print(f"Erro ao carregar encoding do guarda {g.matricula}: {e}")

        if encodings:
            self.index = faiss.IndexFlatL2(len(encodings[0]))
            self.index.add(np.array(encodings))
            self.guardas = valid_guardas
        else:
            print("⚠️ Nenhum encoding válido encontrado.")
            self.index = None

    def search(self, encoding, threshold=0.5):
        if not self.index:
            self.load_index()
        query = np.array([encoding], dtype=np.float32)
        D, I = self.index.search(query, 1)
        if D[0][0] < threshold:
            return self.guardas[I[0][0]]
        return None

face_index = FaceIndex()
