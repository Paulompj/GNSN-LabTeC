import json

# import faiss
import openpyxl
import numpy as np

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum
from django.utils import timezone

from .forms import ForceChangePasswordForm
from camisa.models import Camisa
from guarda.models import Guarda
from pessoa.models import Pessoa


@login_required
def home(request):
    return render(request, "index.html")


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


def fator_equipes(equipe):
    if equipe == "DR":
        return 4
    elif equipe == "SP":
        return 3
    elif equipe == "SE":
        return 3
    elif equipe == "SI":
        return 3
    else:
        return 2


@group_required("super")
def importar_apoio(request):
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")

        if not arquivo:
            messages.error(request, "Selecione um arquivo XLSX.")
            return redirect("app:importarapoio")

        try:
            wb = openpyxl.load_workbook(arquivo)
            sheet = wb.active

            linhas_processadas = 0

            for row in sheet.iter_rows(min_row=2, values_only=True):
                dados = list(row[:12])  # pega só as 12 primeiras colunas
                if len(dados) < 12:
                    continue  # pula linhas incompletas

                (
                    matricula,
                    responsavel,
                    paroquia,
                    municipio,
                    telefone,
                    P,
                    M,
                    G,
                    GG,
                    t3G,
                    t4G,
                    t5G,
                ) = dados

                if not matricula:
                    continue  # pula linhas em branco

                # Cria ou atualiza o GuardaApoio
                apoio, created = GuardaApoio.objects.get_or_create(
                    matricula=str(matricula).strip(),
                    defaults={
                        "responsavel": str(responsavel).strip() if responsavel else "",
                        "paroquia": str(paroquia).strip() if paroquia else "",
                        "municipio": str(municipio).strip() if municipio else "",
                        "telefone": str(telefone).strip() if telefone else "",
                    },
                )

                if not created:
                    # Atualiza os dados, caso já exista
                    apoio.responsavel = (
                        str(responsavel).strip() if responsavel else apoio.responsavel
                    )
                    apoio.paroquia = (
                        str(paroquia).strip() if paroquia else apoio.paroquia
                    )
                    apoio.municipio = (
                        str(municipio).strip() if municipio else apoio.municipio
                    )
                    apoio.telefone = (
                        str(telefone).strip() if telefone else apoio.telefone
                    )
                    apoio.save()

                # Agora insere as camisas por tamanho
                tamanhos_dict = {
                    "P": P,
                    "M": M,
                    "G": G,
                    "GG": GG,
                    "3G": t3G,
                    "4G": t4G,
                    "5G": t5G,
                }

                for tamanho, qtd in tamanhos_dict.items():
                    if qtd and int(qtd) > 0:
                        camisa, _ = CamisaGuardaApoio.objects.update_or_create(
                            apoio=apoio,
                            tamanho=tamanho,
                            defaults={
                                "quantidade": int(qtd),
                                "recebido": False,  # por padrão não recebido
                                "entregador": None,  # ainda não entregue
                                "data": timezone.now(),
                            },
                        )
                linhas_processadas += 1

            messages.success(
                request,
                f"Importação concluída! {linhas_processadas} linhas processadas.",
            )
        except Exception as e:
            messages.error(request, f"Erro ao importar arquivo: {str(e)}")
            return redirect("app:importarapoio")

        return redirect("app:importarapoio")

    return render(request, "importarapoio.html")


def _resolver_username(identificador):
    """Resolve o campo de login (Usuario.usuario) a partir de um identificador
    que pode ser a matrícula do Guarda ou o e-mail da Pessoa."""
    if not identificador:
        return None
    identificador = identificador.strip()

    if "@" in identificador:
        # e-mail da Pessoa -> Usuario vinculado
        try:
            pessoa = Pessoa.objects.select_related("usuario").get(
                email__iexact=identificador
            )
            return pessoa.usuario.usuario
        except ObjectDoesNotExist:
            return None

    # matrícula do Guarda -> Pessoa -> Usuario vinculado
    try:
        guarda = Guarda.objects.select_related("pessoa__usuario").get(
            matricula=identificador
        )
        return guarda.pessoa.usuario.usuario
    except ObjectDoesNotExist:
        return None


def login_guarda(request):
    if request.user.is_authenticated:
        return redirect("app:home")
    if request.method == "POST":
        identificador = request.POST.get("username")
        senha = request.POST.get("senha")

        # O usuário pode informar a matrícula do guarda ou o e-mail da pessoa;
        # ambos são resolvidos para o campo de login (USERNAME_FIELD = "usuario").
        username = _resolver_username(identificador)
        user = (
            authenticate(request, usuario=username, password=senha)
            if username
            else None
        )

        if user is not None:
            login(request, user)
            return redirect("app:home")  # página após login

        messages.warning(request, "Usuário ou senha incorretos.")
    return render(request, "login.html")


def logout_guarda(request):
    logout(request)
    return redirect("app:login")


@login_required
def readapoio(request):
    query = request.GET.get("q", "")
    per_page = int(request.GET.get("per_page", 10))
    status = request.GET.get("status", "pendentes")  # padrão: pendentes

    guardas_qs = GuardaApoio.objects.all()
    if query:
        guardas_qs = guardas_qs.filter(
            Q(responsavel__icontains=query)
            | Q(municipio__icontains=query)
            | Q(paroquia__icontains=query)
        )

    guardas_list = []
    for g in guardas_qs:
        camisas = g.camisas.all()
        total = camisas.aggregate(total=Sum("quantidade"))["total"] or 0
        tamanhos = {c.tamanho: c.quantidade for c in camisas}

        entregue = all(c.recebido for c in camisas) if camisas else False
        entregador = camisas.first().entregador if entregue else None
        data = camisas.first().data if entregue else None

        guardas_list.append(
            {
                "apoio": g,
                "tamanhos": tamanhos,
                "total": total,
                "entregue": entregue,
                "entregador": entregador,
                "data": data,
            }
        )

    # --- FILTRO DE STATUS ---
    if status == "pendentes":
        guardas_list = [g for g in guardas_list if not g["entregue"]]
    elif status == "entregues":
        guardas_list = [g for g in guardas_list if g["entregue"]]
    # caso "todos", não filtra nada

    # --- Paginação ---
    from django.core.paginator import Paginator

    paginator = Paginator(guardas_list, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "readapoio.html",
        {
            "page_obj": page_obj,
            "query": query,
            "status": status,
            "per_page": per_page,
            "per_page_options": [10, 20, 50, 100],
        },
    )


@group_required("super", "Comissão", "Entregador_geral")
def entregar_apoio(request, apoio_id):
    apoio = get_object_or_404(GuardaApoio, id=apoio_id)

    if request.method == "POST":
        observacao = request.POST.get(
            "observacao", ""
        ).strip()  # pega a observação do form

        for camisa in apoio.camisas.all():
            camisa.recebido = True
            camisa.entregador = request.user  # supondo que user -> Guarda
            camisa.data = timezone.now()
            if observacao:
                camisa.observacao = observacao  # salva a observação
            camisa.save()

        messages.success(
            request,
            f"As camisas do guarda de apoio {apoio.responsavel} foram entregues!",
        )
        return redirect("app:readapoio")

    return redirect("app:readapoio")


@login_required
def relatorio_apoio(request):
    ano = request.GET.get("ano")

    # Definir equipes
    equipe_saude_paroquias = [
        "EQUIPE DE APOIO SAÚDE"
    ]  # ajustar conforme os nomes reais de paroquias de saúde

    # Filtrar guardas
    guardas = GuardaApoio.objects.all()

    tamanhos_list = ["PP", "P", "M", "G", "GG", "3G", "4G", "5G", "6G"]

    # Dicionário para agregar por equipe e tamanho
    agregados = {}

    for g in guardas:
        # Identificar equipe
        if g.paroquia in equipe_saude_paroquias:
            equipe = "Equipe Saúde"
        else:
            equipe = "Guarda Apoio"

        if equipe not in agregados:
            agregados[equipe] = {
                t: {"entregues": 0, "a_entregar": 0} for t in tamanhos_list
            }

        camisas = g.camisas.all()
        for t in tamanhos_list:
            entregues = (
                camisas.filter(tamanho=t, recebido=True).aggregate(
                    qtd=Sum("quantidade")
                )["qtd"]
                or 0
            )
            a_entregar = (
                camisas.filter(tamanho=t, recebido=False).aggregate(
                    qtd=Sum("quantidade")
                )["qtd"]
                or 0
            )
            agregados[equipe][t]["entregues"] += entregues
            agregados[equipe][t]["a_entregar"] += a_entregar

    # Preparar dados para a tabela (lista de linhas)
    tabela_dados = []
    total_geral = {t: {"entregues": 0, "a_entregar": 0} for t in tamanhos_list}

    for equipe, tamanhos in agregados.items():
        total_equipe = {"entregues": 0, "a_entregar": 0}
        for t, qtds in tamanhos.items():
            tabela_dados.append(
                {
                    "equipe": equipe,
                    "tamanho": t,
                    "entregues": qtds["entregues"],
                    "a_entregar": qtds["a_entregar"],
                }
            )
            # acumula total por equipe
            total_equipe["entregues"] += qtds["entregues"]
            total_equipe["a_entregar"] += qtds["a_entregar"]
            # acumula total geral
            total_geral[t]["entregues"] += qtds["entregues"]
            total_geral[t]["a_entregar"] += qtds["a_entregar"]

        # adiciona linha de total por equipe
        tabela_dados.append(
            {
                "equipe": f"Total {equipe}",
                "tamanho": "-",
                "entregues": total_equipe["entregues"],
                "a_entregar": total_equipe["a_entregar"],
            }
        )

    # adiciona linha de total geral
    tabela_dados.append(
        {
            "equipe": "Total Geral",
            "tamanho": "-",
            "entregues": sum([v["entregues"] for v in total_geral.values()]),
            "a_entregar": sum([v["a_entregar"] for v in total_geral.values()]),
        }
    )

    # Preparar dados para gráficos
    entregues_por_equipe = {
        e: sum([v["entregues"] for v in t.values()]) for e, t in agregados.items()
    }
    entregues_por_tamanho = {
        t: sum([v[t]["entregues"] for v in agregados.values()]) for t in tamanhos_list
    }
    a_entregar_por_equipe = {
        e: sum([v["a_entregar"] for v in t.values()]) for e, t in agregados.items()
    }
    a_entregar_por_tamanho = {
        t: sum([v[t]["a_entregar"] for v in agregados.values()]) for t in tamanhos_list
    }
    totais_por_equipe = {
        e: entregues_por_equipe[e] + a_entregar_por_equipe[e]
        for e in entregues_por_equipe
    }
    totais_por_tamanho = {
        t: entregues_por_tamanho[t] + a_entregar_por_tamanho[t] for t in tamanhos_list
    }

    # Equipe x Tamanho (linha empilhada)
    entregues_por_equipe_tamanho = {
        e: {t: v["entregues"] for t, v in tamanhos.items()}
        for e, tamanhos in agregados.items()
    }
    a_entregar_por_equipe_tamanho = {
        e: {t: v["a_entregar"] for t, v in tamanhos.items()}
        for e, tamanhos in agregados.items()
    }
    totais_por_equipe_tamanho = {
        e: {t: v["entregues"] + v["a_entregar"] for t, v in tamanhos.items()}
        for e, tamanhos in agregados.items()
    }

    anos_qs = CamisaGuardaApoio.objects.exclude(data__isnull=True).values_list(
        "data", flat=True
    )
    anos = sorted(list({d.year for d in anos_qs if d is not None}), reverse=True)
    ano_selecionado = ano

    return render(
        request,
        "relatorio_apoio.html",
        {
            "tabela_dados": tabela_dados,
            "entregues_por_equipe": entregues_por_equipe,
            "entregues_por_tamanho": entregues_por_tamanho,
            "entregues_por_equipe_tamanho": entregues_por_equipe_tamanho,
            "a_entregar_por_equipe": a_entregar_por_equipe,
            "a_entregar_por_tamanho": a_entregar_por_tamanho,
            "a_entregar_por_equipe_tamanho": a_entregar_por_equipe_tamanho,
            "totais_por_equipe": totais_por_equipe,
            "totais_por_tamanho": totais_por_tamanho,
            "totais_por_equipe_tamanho": totais_por_equipe_tamanho,
            "anos": anos,
            "ano_selecionado": ano_selecionado,
        },
    )


@login_required
def force_change_password(request):
    user = request.user

    if request.method == "POST":
        form = ForceChangePasswordForm(request.POST)
        if form.is_valid():
            senha = form.cleaned_data["new_password1"]
            user.set_password(senha)
            user.trocar_senha = False
            user.save()
            update_session_auth_hash(request, user)  # mantém o login
            messages.success(request, "Senha alterada com sucesso!")
            return redirect("app:home")
    else:
        form = ForceChangePasswordForm()

    return render(request, "forcedpassword.html", {"form": form})


@login_required
def monitoramento(request):
    ano = request.GET.get("ano")
    qs = Camisa.objects.filter(situacao=True)
    if ano:
        qs = qs.filter(ano=ano)

    cores_equipe = {
        "E1": "#f4b000",
        "E2": "#e85c2a",
        "E3": "#7ab731",
        "E4": "#3fa9f5",
        "E5": "#d22f27",
        "RB": "#1c3b6b",
        "NB": "#f2e2b3",
        "FC": "#f5f1d7",
        "PS": "#8b5c3f",
        "AT": "#444444",
        "NC": "#2e98a7",
        "ASCOM": "#212529",
        "BS": "#212529",
        "CP": "#212529",
        "DR": "#212529",
        "ES": "#212529",
        "SE": "#212529",
        "SI": "#212529",
    }

    def fator_equipes(equipe):
        if equipe == "DR":
            return 4
        elif equipe in ["SP", "SE", "SI"]:
            return 3
        else:
            return 2

    equipes_data = []
    equipes = qs.values("equipe").distinct()

    for e in equipes:
        equipe = e["equipe"]
        # Número de guardas (sem fator)
        total_guardas = qs.filter(equipe=equipe).count()
        recebidos_guardas = qs.filter(equipe=equipe, recebido=True).count()
        cor = cores_equipe.get(equipe, "#e6e6e6")
        equipes_data.append(
            {
                "equipe": equipe,
                "total_guardas": total_guardas,
                "recebidos_guardas": recebidos_guardas,
                "nao_recebidos_guardas": total_guardas - recebidos_guardas,
                "cor": cor,
            }
        )

    # Total de camisas entregues ponderado pelo fator
    total_camisas_entregues = sum(
        fator_equipes(c.equipe) for c in qs.filter(recebido=True)
    )

    # Total geral de guardas para gráfico
    total_geral_guardas = qs.count()
    recebidos_geral_guardas = qs.filter(recebido=True).count()

    total_guardas_receberam = (
        qs.filter(recebido=True).values("guarda").distinct().count()
    )

    context = {
        "equipes_data": json.dumps(equipes_data),
        "geral_data": json.dumps(
            {
                "total_guardas": total_geral_guardas,
                "recebidos_guardas": recebidos_geral_guardas,
                "nao_recebidos_guardas": total_geral_guardas - recebidos_geral_guardas,
            }
        ),
        "total_guardas_receberam": total_guardas_receberam,
        "total_camisas_entregues": total_camisas_entregues,
    }

    return render(request, "monitoramento.html", context)


# def carregar_faiss_index():
#     """
#     Carrega todos os encodings do banco de dados e cria um índice FAISS na RAM.
#     """
#     guardas = Guarda.objects.exclude(encoding__isnull=True)
#     if not guardas:
#         return None, [], []

#     encodings = []
#     ids = []
#     for g in guardas:
#         try:
#             enc = np.frombuffer(g.encoding, dtype=np.float64)
#             encodings.append(enc)
#             ids.append(g.idguarda)
#         except Exception:
#             continue

#     encodings = np.array(encodings).astype("float32")
#     index = faiss.IndexFlatL2(encodings.shape[1])  # busca por distância euclidiana
#     index.add(encodings)
#     return index, ids, encodings
