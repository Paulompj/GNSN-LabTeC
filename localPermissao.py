from django.contrib.auth.models import Group
from app.models import Guarda  # troque "app" pelo nome do seu app

# pega o grupo "Comissão" já existente
#grupo = Group.objects.get(name="Comissão")
grupo = Group.objects.get(name="Patrimonio_solicitante")

# lista de matrículas dos guardas que vão receber permissão
matriculas = [
#    2226, 1599, 3245, 111, 1795, 1791, 2514, 1290, 3081, 3103, 2676, 1702, 1292, 1772, 2446, 3351, 3544, 2563, 2563,
#    2056, 1312, 2786, 1751, 2168, 1780, 1535, 2374, 305, 2580, 1019, 86, 1535, 2204, 2389, 1019, 3049, 1535, 169,
#    796, 1763, 796, 1759, 2234, 1543, 1543, 2152, 3351, 137, 2666, 1751
    83, 111, 137, 169, 209, 464, 658, 862, 927, 1019, 1120, 1127, 1277, 1364, 1500, 1702, 1717, 1753, 1772, 1795, 2093,
    2096, 2126, 2152, 2268, 2438, 2442, 2563, 2580, 2642, 2667, 2676, 2680, 2691, 2716, 2774, 2775, 2815, 3023, 3049,
    3067, 3072, 3081, 3103, 3119, 3153, 3189, 3238, 3245, 3325, 3331, 3354, 3417, 3422, 3508, 3544, 3591
]

for mat in matriculas:
    try:
        guarda = Guarda.objects.get(matricula=mat)
        guarda.groups.add(grupo)  # adiciona ao grupo Comissão
        if guarda.must_change_password:
            guarda.set_password("Guarda2025@")  # senha padrão
            guarda.must_change_password = True  # força troca no 1º login
            print(f"✅ {guarda.nome} ({mat}) senha resetada")
        guarda.save()
        print(f"✅ {guarda.nome} ({mat}) atualizado com Comissão")
    except Guarda.DoesNotExist:
        print(f"❌ Guarda com matrícula {mat} não encontrado")
