import re
import cv2
import json
import base64
import openpyxl
import numpy as np

# não usado localmente
# import face_recognition

from datetime import datetime
from collections import OrderedDict

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, OuterRef, Subquery, Max, Count
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render


from .forms import GuardaForm, GuardaGroupForm
from app.faiss_index import face_index
from camisa.models import Camisa
from .models import Guarda


def group_required(*group_names):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if (
                request.user.is_authenticated
                and request.user.groups.filter(name__in=group_names).exists()
            ):
                return view_func(request, *args, **kwargs)
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect("app:home")

        return _wrapped_view

    return decorator


@login_required
def home(request):
    return render(request, "index.html")


@group_required("super", "Direção")
def createguarda(request, idguarda=None):
    if idguarda:
        guarda = get_object_or_404(Guarda, idguarda=idguarda)
        form = GuardaForm(request.POST or None, request.FILES or None, instance=guarda)
    else:
        form = GuardaForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            guarda = form.save(commit=False)

            # Se a foto foi atualizada, recalcula o encoding
            if "foto" in form.changed_data and guarda.foto:
                imagem = face_recognition.load_image_file(guarda.foto.path)
                rostos = face_recognition.face_encodings(imagem)
                if rostos:
                    guarda.encoding = np.array(rostos[0], dtype=np.float32).tobytes()

            guarda.save()
            face_index.load_index()  # atualiza FAISS
            messages.success(request, f"Guarda {guarda.nome} salvo com sucesso!")
            return redirect("app:readguarda")

    return render(request, "guarda/createguarda.html", {"form": form})


@group_required("super", "Direção")
def readguarda(request):
    search = request.GET.get("search", "")
    per_page = request.GET.get("per_page", 10)
    sort = request.GET.get("sort", "nome")
    direction = request.GET.get("direction", "asc")

    try:
        per_page = int(per_page)
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Subquery para a camisa mais recente
    camisas_recents = Camisa.objects.filter(guarda=OuterRef("pk")).order_by("-ano")

    # Queryset base
    guardas_qs = Guarda.objects.all().annotate(
        equipe_recente=Subquery(camisas_recents.values("equipe")[:1]),
        tamcamisa_recente=Subquery(camisas_recents.values("tamcamisa")[:1]),
    )

    # Filtro de busca
    if search:
        guardas_qs = guardas_qs.filter(
            Q(nome__icontains=search)
            | Q(matricula__icontains=search)
            | Q(cpf__icontains=search)
        )

    # Converte para lista para manipular permissões
    guardas_list = list(guardas_qs)

    for g in guardas_list:
        grupos = list(g.groups.values_list("name", flat=True))
        g.grupos = grupos
        g.first_group_name = grupos[0] if grupos else ""

    # Ordenação
    valid_sorts = {
        "matricula": lambda x: x.matricula or "",
        "nome": lambda x: x.nome or "",
        "cpf": lambda x: x.cpf or "",
        "equipe_recente": lambda x: x.equipe_recente or "",
        "tamcamisa_recente": lambda x: x.tamcamisa_recente or "",
        "grupos": lambda x: x.first_group_name,
    }
    sort_func = valid_sorts.get(sort, valid_sorts["nome"])
    reverse = direction == "desc"
    guardas_list.sort(key=sort_func, reverse=reverse)

    # Paginação
    paginator = Paginator(guardas_list, per_page)
    page_number = request.GET.get("page")
    guardas_page = paginator.get_page(page_number)

    return render(
        request,
        "guarda/readguarda.html",
        {
            "guardas": guardas_page,
            "request": request,
            "sort": sort,
            "direction": direction,
        },
    )


@group_required("super", "Direção")
def passwordguarda(request, idguarda):
    guarda = get_object_or_404(Guarda, idguarda=idguarda)

    if request.method == "POST":
        senha = request.POST.get("senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        # Validação básica
        if not senha or not confirmar_senha:
            messages.error(request, "Preencha ambos os campos de senha.")
        elif senha != confirmar_senha:
            messages.error(request, "As senhas não coincidem.")
        else:
            # Validação da senha forte
            if len(senha) < 8:
                messages.error(request, "A senha deve ter pelo menos 8 caracteres.")
            elif not re.search(r"[A-Z]", senha):
                messages.error(
                    request, "A senha deve conter pelo menos uma letra maiúscula."
                )
            elif not re.search(r"[a-z]", senha):
                messages.error(
                    request, "A senha deve conter pelo menos uma letra minúscula."
                )
            elif not re.search(r"[0-9]", senha):
                messages.error(request, "A senha deve conter pelo menos um número.")
            elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
                messages.error(
                    request, "A senha deve conter pelo menos um caractere especial."
                )
            else:
                # Tudo ok, salvar senha
                guarda.set_password(senha)
                guarda.must_change_password = True
                guarda.save()
                messages.success(
                    request, f"Senha cadastrada com sucesso para {guarda.nome}!"
                )
                return redirect("guarda:readguarda")

    return render(request, "guarda/passwordguarda.html", {"guarda": guarda})


@group_required("super", "Direção")
def permissoes(request, idguarda):
    guarda = get_object_or_404(Guarda, idguarda=idguarda)

    if request.method == "POST":
        form = GuardaGroupForm(request.POST, instance=guarda)
        if form.is_valid():
            if request.POST.get("reset_senha"):
                guarda.set_password("Guarda2025@")
                guarda.must_change_password = True
                guarda.save()
                form.save()
                messages.success(
                    request,
                    f"Permissões atualizadas para {guarda.nome} e Senha resetada para: Guarda2025@",
                )
            else:
                form.save()
                messages.success(request, f"Permissões atualizadas para {guarda.nome}.")
            return redirect("guarda:readguarda")  # ou outra página de listagem
    else:
        form = GuardaGroupForm(instance=guarda)

    return render(request, "guarda/permissoes.html", {"form": form, "guarda": guarda})


@group_required("super")
def importaguardas(request):
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            messages.error(request, "Selecione um arquivo XLSX para importar.")
            return redirect("app:importaguardas")

        # Mapeamento de estado civil
        estado_civil_map = {
            "0": "solteiro",
            "1": "casado",
            "2": "separado",
            "3": "divorciado",
            "4": "viuvo",
            "5": "uniao_estavel",
        }

        try:
            wb = openpyxl.load_workbook(arquivo)
            sheet = wb.active

            count_created = 0
            count_updated = 0

            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if i == 0:
                    # Ignora cabeçalho
                    continue

                matricula = row[0]  # CAD_MATRICULA
                nome = row[1]  # CAD_NOME
                rg = row[3]  # CAD_RG
                cpf = row[4]  # CAD_CPF
                estado_civil = str(row[5]).strip()  # CAD_EST_CIVIL
                nascimento_valor = row[6]  # CAD_NASC
                try:
                    nascimento = datetime.strptime(
                        str(nascimento_valor).split(" ")[0], "%Y-%m-%d"
                    ).date()
                except (ValueError, TypeError):
                    nascimento = None
                telefone = row[7]  # CAD_TEL_RES
                celular = row[8]  # CAD_TEL_CEL
                tel_comercial = row[9]  # CAD_TEL_COM
                email = row[10]  # CAD_EMAIL
                cep = row[11]  # CAD_CEP
                endereco = row[12]  # CAD_END
                bairro = row[13]  # CAD_BAI
                cidade = row[14]  # CAD_CID
                uf = row[15]  # CAD_UF
                complemento = row[16]  # CAD_COMP
                cad_sit = str(row[17]).strip()  # CAD_SIT
                observacao = row[18] if row[18] else ""  # CAD_OBS

                if not matricula:
                    continue

                # Ajusta ativo/inativo
                is_active = True if cad_sit == "0" else False

                # Ajusta estado civil
                estado_civil_val = estado_civil_map.get(estado_civil, None)

                # Ajusta sexo
                sexo = "M"

                # Ajusta nascimento
                if nascimento:
                    nascimento_val = str(nascimento).split(" ")[0]  # remove hora
                else:
                    nascimento_val = None

                # Extrai matrícula do padrinho do campo observacao
                observacao_str = str(observacao) if observacao else ""
                padrinho_match = re.search(r"_(\d+)$", observacao_str)
                matricula_padrinho = (
                    int(padrinho_match.group(1)) if padrinho_match else None
                )

                # Atualiza ou cria guarda
                guarda, created = Guarda.objects.update_or_create(
                    matricula=matricula,
                    defaults={
                        "nome": nome if nome else "NOME NÃO INFORMADO",
                        "rg": rg if rg else "0",
                        "cpf": cpf if cpf else "0",
                        "estado_civil": estado_civil_val,
                        "nascimento": nascimento_val,
                        "telefone": telefone if telefone else None,
                        "celular": celular if celular else None,
                        "tel_comercial": tel_comercial if tel_comercial else None,
                        "email": email if email else None,
                        "cep": cep if cep else None,
                        "endereco": endereco if endereco else None,
                        "bairro": bairro if bairro else None,
                        "cidade": cidade if cidade else None,
                        "UF": uf if uf else None,
                        "complemento": complemento if complemento else None,
                        "observacao": observacao if observacao else None,
                        "is_active": is_active,
                        "sexo": sexo,
                        "matricula_padrinho": matricula_padrinho,
                    },
                )

                if created:
                    count_created += 1
                else:
                    count_updated += 1

            messages.success(
                request,
                f"Importação concluída: {count_created} guardas criados, {count_updated} guardas atualizados.",
            )
            return redirect("app:importaguardas")

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {str(e)}")
            return redirect("app:importaguardas")

    return render(request, "guarda/importaguardas.html")


@login_required()
def relatorio_geral(request):
    if request.method == "GET":
        ano = request.GET.get("ano")
    if not ano:
        ano = Camisa.objects.aggregate(Max("ano"))["ano__max"]
    else:
        ano = 2025

    camisas_aptas = Camisa.objects.filter(situacao=True, ano=ano)

    entregues_por_equipe = {}
    entregues_por_tamanho = {}
    entregues_por_equipe_tamanho = {}

    a_entregar_por_equipe = {}
    a_entregar_por_tamanho = {}
    a_entregar_por_equipe_tamanho = {}

    totais_por_equipe = {}
    totais_por_tamanho = {}
    totais_por_equipe_tamanho = {}

    tabela_dados = []

    anos = Camisa.objects.filter(situacao=True).values_list("ano", flat=True).distinct()
    equipes = camisas_aptas.values_list("equipe", flat=True).distinct()
    tamanhos = camisas_aptas.values_list("tamcamisa", flat=True).distinct()

    ordem_tamanhos = [
        "PP",
        "P",
        "M",
        "G",
        "GG",
        "XG",
        "XGG",
        "3G",
        "4G",
        "5G",
        "6G",
        "ESPECIAL",
    ]

    for equipe in equipes:
        for tamanho in tamanhos:
            total_aptos = camisas_aptas.filter(equipe=equipe, tamcamisa=tamanho).count()
            total_entregues = camisas_aptas.filter(
                equipe=equipe, tamcamisa=tamanho, recebido=True
            ).count()
            a_entregar = total_aptos - total_entregues

            if total_aptos > 0:
                tabela_dados.append(
                    {
                        "equipe": equipe,
                        "tamanho": tamanho,
                        "entregues": total_entregues,
                        "a_entregar": a_entregar,
                    }
                )

                # Entregues
                entregues_por_equipe[equipe] = (
                    entregues_por_equipe.get(equipe, 0) + total_entregues
                )
                entregues_por_tamanho[tamanho] = (
                    entregues_por_tamanho.get(tamanho, 0) + total_entregues
                )
                entregues_por_equipe_tamanho.setdefault(equipe, {})[
                    tamanho
                ] = total_entregues

                # A entregar
                a_entregar_por_equipe[equipe] = (
                    a_entregar_por_equipe.get(equipe, 0) + a_entregar
                )
                a_entregar_por_tamanho[tamanho] = (
                    a_entregar_por_tamanho.get(tamanho, 0) + a_entregar
                )
                a_entregar_por_equipe_tamanho.setdefault(equipe, {})[
                    tamanho
                ] = a_entregar

                # Totais
                totais_por_equipe[equipe] = (
                    totais_por_equipe.get(equipe, 0) + total_aptos
                )
                totais_por_tamanho[tamanho] = (
                    totais_por_tamanho.get(tamanho, 0) + total_aptos
                )
                totais_por_equipe_tamanho.setdefault(equipe, {})[tamanho] = total_aptos

    # Adicionar linha de totais na tabela
    total_entregues_all = sum([row["entregues"] for row in tabela_dados])
    total_a_entregar_all = sum([row["a_entregar"] for row in tabela_dados])
    tabela_dados.append(
        {
            "equipe": "TOTAL",
            "tamanho": "-",
            "entregues": total_entregues_all,
            "a_entregar": total_a_entregar_all,
        }
    )

    # Ordenação: por equipe (alfabética), e por tamanho na ordem definida
    tabela_dados = sorted(
        tabela_dados,
        key=lambda x: (
            x["equipe"] if x["equipe"] != "TOTAL" else "ZZZZ",  # TOTAL vai pro fim
            (
                ordem_tamanhos.index(x["tamanho"])
                if x["tamanho"] in ordem_tamanhos
                else 999
            ),
        ),
    )

    context = {
        "entregues_por_equipe": json.dumps(entregues_por_equipe),
        "entregues_por_tamanho": json.dumps(entregues_por_tamanho),
        "entregues_por_equipe_tamanho": json.dumps(entregues_por_equipe_tamanho),
        "a_entregar_por_equipe": json.dumps(a_entregar_por_equipe),
        "a_entregar_por_tamanho": json.dumps(a_entregar_por_tamanho),
        "a_entregar_por_equipe_tamanho": json.dumps(a_entregar_por_equipe_tamanho),
        "totais_por_equipe": json.dumps(totais_por_equipe),
        "totais_por_tamanho": json.dumps(totais_por_tamanho),
        "totais_por_equipe_tamanho": json.dumps(totais_por_equipe_tamanho),
        "tabela_dados": tabela_dados,
        "anos": anos,
    }
    return render(request, "guarda/relatorio_geral.html", context)


@login_required()
def relatorio_entregas(request):
    anos_disponiveis = (
        Camisa.objects.values_list("ano", flat=True).distinct().order_by("ano")
    )
    ano = request.GET.get("ano")
    if not ano:
        ano = Camisa.objects.aggregate(Max("ano"))["ano__max"]
    dias_selecionados = request.GET.getlist("data")  # multi-select

    labels = []
    data = []
    tabela_camisas = OrderedDict()
    total_geral = 0

    # Apenas entregas realizadas
    camisas_qs = Camisa.objects.filter(recebido=True)

    if ano:
        camisas_qs = camisas_qs.filter(ano=ano)

    # Extrai apenas a parte da data
    camisas_qs = camisas_qs.annotate(dia=TruncDate("data"))

    # Lista de dias únicos
    dias_entregas = camisas_qs.values_list("dia", flat=True).distinct().order_by("dia")

    if dias_selecionados:
        camisas_qs = camisas_qs.filter(dia__in=dias_selecionados)

    if camisas_qs.exists():
        # Gráfico - entregadores
        guardas = Guarda.objects.annotate(
            qtd=Count("camisas_entregues", filter=Q(camisas_entregues__in=camisas_qs))
        ).filter(qtd__gt=0)

        labels = []
        data = []
        for g in guardas:
            entregas = camisas_qs.filter(entregador=g)
            qtd_total = entregas.count()
            if qtd_total > 0:
                labels.append(g.nome)
                data.append(qtd_total)

        # Tabela de camisas por tamanho
        ordem_tamanhos = [
            "PP",
            "P",
            "M",
            "G",
            "GG",
            "XG",
            "XGG",
            "3G",
            "4G",
            "5G",
            "6G",
            "ESPECIAL",
        ]
        for tam in ordem_tamanhos:
            qs_tam = camisas_qs.filter(tamcamisa=tam)
            if qs_tam.exists():
                equipes = (
                    qs_tam.values("equipe").annotate(qtd=Count("id")).order_by("equipe")
                )

                equipes_corrigidas = []
                total_por_tam = 0
                for e in equipes:
                    qtd_corrigida = e["qtd"]  # * fator_equipes(e['equipe'])
                    equipes_corrigidas.append(
                        {"equipe": e["equipe"], "qtd": qtd_corrigida}
                    )
                    total_por_tam += qtd_corrigida

                tabela_camisas[tam] = {
                    "equipes": equipes_corrigidas,
                    "total": total_por_tam,
                }
                total_geral += total_por_tam

    context = {
        "anos_disponiveis": anos_disponiveis,
        "ano_selecionado": ano,
        "dias_entregas": dias_entregas,
        "dias_selecionados": dias_selecionados,
        "labels": labels,
        "data": data,
        "tabela_camisas": tabela_camisas,
        "total_geral": total_geral,
    }

    return render(request, "guarda/relatorio_entregas.html", context)


@login_required()
def relatorio_por_equipe(request):
    ano = request.GET.get("ano")
    if not ano:
        ano = Camisa.objects.aggregate(Max("ano"))["ano__max"]

    # Pega todos os anos distintos disponíveis
    anos_disponiveis = (
        Camisa.objects.filter(situacao=True)
        .values_list("ano", flat=True)
        .distinct()
        .order_by("ano")
    )

    # Ano padrão
    if not ano and anos_disponiveis:
        ano = anos_disponiveis[0]

    camisas_aptas = Camisa.objects.filter(situacao=True, ano=ano)

    equipes = sorted(camisas_aptas.values_list("equipe", flat=True).distinct())
    tamanhos_ordem = [
        "PP",
        "P",
        "M",
        "G",
        "GG",
        "XG",
        "XGG",
        "3G",
        "4G",
        "5G",
        "6G",
        "ESPECIAL",
    ]

    dados_por_equipe = {}

    for equipe in equipes:
        dados_por_equipe[equipe] = {}
        camisas_equipe = camisas_aptas.filter(equipe=equipe)
        for tamanho in tamanhos_ordem:
            total = camisas_equipe.filter(tamcamisa=tamanho).count()
            if total > 0:
                entregues = camisas_equipe.filter(
                    tamcamisa=tamanho, recebido=True
                ).count()
                a_entregar = total - entregues
                dados_por_equipe[equipe][tamanho] = {
                    "entregues": entregues,
                    "a_entregar": a_entregar,
                }

    context = {
        "ano": ano,
        "anos_disponiveis": anos_disponiveis,
        "equipes": equipes,
        "tamanhos_ordem": tamanhos_ordem,
        "dados_por_equipe": json.dumps(dados_por_equipe),
    }
    return render(request, "guarda/relatorio_por_equipe.html", context)


@group_required("super", "Direção")
@csrf_exempt
def reconhecimento_facial(request):
    if request.method == "GET":
        # Renderiza o HTML da câmera
        return render(request, "guarda/reconhecimento.html")

    elif request.method == "POST":
        try:
            data = request.POST.get("imagem")
            if not data:
                return JsonResponse(
                    {"status": "erro", "mensagem": "Imagem não enviada."}
                )

            # Decodifica a imagem base64
            img_bytes = base64.b64decode(data.split(",")[1])
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(
                frame_rgb, (0, 0), fx=0.5, fy=0.5
            )  # reduz ruído, aumenta performance

            # Extrai encodings do rosto
            encodings = face_recognition.face_encodings(frame_resized)
            if not encodings:
                return JsonResponse(
                    {"status": "erro", "mensagem": "Nenhum rosto detectado."}
                )

            # Busca no índice FAISS
            guarda = face_index.search(encodings[0], threshold=0.35)
            if guarda:
                return JsonResponse(
                    {
                        "status": "ok",
                        "guarda": {
                            "nome": guarda.nome,
                            "matricula": guarda.matricula,
                            "foto_url": guarda.foto.url if guarda.foto else None,
                        },
                    }
                )
            else:
                return JsonResponse(
                    {"status": "erro", "mensagem": "Rosto não reconhecido."}
                )

        except Exception as e:

            return JsonResponse({"status": "erro", "mensagem": str(e)})

    else:
        return JsonResponse(
            {"status": "erro", "mensagem": "Método inválido."}, status=405
        )
