# script_apto.py
from app.models import Guarda, Camisa  # troque sua_app pelo nome correto

# 👉 lista com as 105 matrículas
matriculas = [
    210, 275, 307, 425, 507, 582, 630, 650, 786, 814, 875, 900, 1003, 1025, 1051, 1196, 1196, 1207, 1262, 1278, 1297,
    1329, 1432, 1437, 1522, 1524, 1534, 1573, 1729, 1745, 1768, 1773, 1781, 1783, 1797, 1812, 1843, 1843, 1843, 1854,
    1907, 2015, 2038, 2055, 2057, 2081, 2103, 2131, 2146, 2147, 2148, 2148, 2162, 2165, 2172, 2193, 2253, 2279, 2290,
    2336, 2349, 2380, 2395, 2492, 2589, 2592, 2626, 2630, 2663, 2674, 2687, 2706, 2729, 2738, 3016, 3034, 3054, 3057,
    3069, 3074, 3086, 3096, 3097, 3102, 3139, 3154, 3156, 3233, 3269, 3269, 3313, 3429, 3432, 3438, 3444, 3462, 3492,
    3540, 3595, 3597, 3646, 3677, 4016, 2823, 3629
]

def tornar_camisas_aptas():
    for m in matriculas:
        try:
            guarda = Guarda.objects.get(matricula=m)
        except Guarda.DoesNotExist:
            print(f"❌ Guarda não encontrado: matrícula {m}")
            continue

        camisas = Camisa.objects.filter(guarda=guarda)

        if not camisas.exists():
            print(f"⚠️ Guarda {guarda.nome} ({m}) não possui camisas cadastradas.")
            continue

        for camisa in camisas:
            if camisa.situacao:
                print(f"✅ Já estava apto -> {guarda.nome} ({m}), Ano {camisa.ano}, Tam {camisa.tamcamisa}")
            else:
                print(f"🔄 Alterando -> {guarda.nome} ({m}), Ano {camisa.ano}, Tam {camisa.tamcamisa} de INAPTO → APTO")
                camisa.situacao = True
                camisa.save()

tornar_camisas_aptas()
