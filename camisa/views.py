import json
import openpyxl

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from django.db.models import F, Q, Count
from django.db.models.functions import TruncDate

from .forms import CamisaForm
from .models import Guarda, Camisa, CamisaLog

from collections import OrderedDict
from datetime import datetime


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


@login_required
def home(request):
    return render(request, "index.html")


@login_required
def findcamisa(request):
    anos = Camisa.objects.filter(situacao=True).values_list("ano", flat=True).distinct()
    error = None

    # Últimas 20 camisas entregues
    ultimas_camisas = Camisa.objects.filter(recebido=True).order_by("-data")[:20]

    # Guarda logado (entregador)
    guarda_logado = get_object_or_404(Guarda, matricula=request.user.matricula)

    if request.method == "POST":
        matricula = request.POST.get("matricula")
        ano = request.POST.get("ano")
        camisa_guarda_logado = Camisa.objects.get(guarda=guarda_logado, ano=ano)

        try:
            guarda = Guarda.objects.get(matricula=matricula)
        except Guarda.DoesNotExist:
            error = "Guarda não encontrado."
            return render(
                request,
                "camisa/findcamisa.html",
                {"anos": anos, "error": error, "ultimas_camisas": ultimas_camisas},
            )

        try:
            camisa = Camisa.objects.get(guarda=guarda, ano=ano)
        except Camisa.DoesNotExist:
            error = f"Nenhuma camisa encontrada para o guarda {guarda.nome} no ano de {ano}."
            return render(
                request,
                "camisa/findcamisa.html",
                {"anos": anos, "error": error, "ultimas_camisas": ultimas_camisas},
            )

        mesma_equipe = camisa.equipe == camisa_guarda_logado.equipe
        grupo_entrega_geral = request.user.groups.filter(
            name="Entregador_geral"
        ).exists()
        print(grupo_entrega_geral)

        if not mesma_equipe and not grupo_entrega_geral:
            error = (
                f"O usuário {guarda_logado.nome} não pode entregar camisa "
                f"da equipe {camisa.equipe}."
            )
            return render(
                request,
                "camisa/findcamisa.html",
                {"anos": anos, "error": error, "ultimas_camisas": ultimas_camisas},
            )

        if not camisa.situacao:  # INAPTO
            error = f"O guarda {guarda.nome} no ano de {ano} está INAPTO!"
        elif camisa.recebido:  # RECEBIDO
            error = f"A camisa do guarda {guarda.nome} no ano de {ano} já foi entregue para {camisa.recebedor} por {camisa.entregador}."
        else:
            request.session["guarda_id"] = guarda.idguarda
            request.session["camisa_id"] = camisa.id
            return redirect("app:takecamisa")

    return render(
        request,
        "camisa/findcamisa.html",
        {"anos": anos, "error": error, "ultimas_camisas": ultimas_camisas},
    )


@login_required
def minhas_entregas(request):
    user = request.user

    # pega apenas entregas feitas pelo usuário logado
    camisas = Camisa.objects.filter(entregador=user)

    # parâmetros de paginação
    per_page = request.GET.get("per_page", "10")
    page_number = request.GET.get("page")

    if per_page == "all":
        page_obj = camisas  # manda todos
    else:
        paginator = Paginator(camisas, int(per_page))
        page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "per_page_options": [10, 25, 50, 100],
    }
    return render(request, "camisa/minhas_entregas.html", context)


@login_required
def takecamisa(request):
    guarda_id = request.session.pop("guarda_id", None)
    camisa_id = request.session.pop("camisa_id", None)
    if not guarda_id or not camisa_id:
        return redirect("app:findcamisa")  # se não houver dados
    # buscar objetos no banco
    guarda = Guarda.objects.get(idguarda=guarda_id)
    print(camisa_id)
    camisa = Camisa.objects.get(id=camisa_id)
    return render(
        request, "camisa/takecamisa.html", {"guarda": guarda, "camisa": camisa}
    )


@login_required
def entregar_camisa(request):
    if request.method == "POST":
        guarda_id = request.POST.get("guarda_id")
        camisa_id = request.POST.get("camisa_id")
        proprio = request.POST.get("mesmo")  # checkbox do HTML
        recebedor = request.POST.get("recebedor", "").strip()
        termo = request.FILES.get("termo")
        procuracao = request.FILES.get("procuracao")

        guarda = get_object_or_404(Guarda, idguarda=guarda_id)
        camisa = get_object_or_404(Camisa, id=camisa_id)

        # Se for o próprio
        if proprio:
            recebedor = guarda.nome
        else:
            # Validar se informou recebedor
            if not recebedor:
                messages.error(
                    request, "Informe o nome do recebedor ou marque 'É o próprio'."
                )
                return redirect("app:takecamisa")

            # Exigir procuração se não for o próprio
            # if not procuracao:
            #    messages.error(request, "É obrigatório anexar a procuração quando o recebedor não é o próprio.")
            #    return redirect("app:takecamisa")

        # Salvar arquivos
        if termo:
            camisa.arquivo = termo
        if procuracao:
            camisa.procuracao = procuracao

        camisa.recebido = True
        camisa.recebedor = recebedor
        camisa.entregador = request.user
        camisa.data = timezone.now()
        camisa.save()

        messages.success(
            request,
            f"A camisa do guarda {guarda.nome} foi entregue com sucesso para {recebedor}!",
        )
        return redirect("app:takecamisa")

    return redirect("app:takecamisa")


@group_required("super", "Direção")
def changecamisa(request, idcamisa):
    try:
        camisa = get_object_or_404(Camisa, id=idcamisa)
    except Http404:
        camisa = get_object_or_404(Camisa, id=idcamisa)

    tamanhos_camisa = ["PP", "P", "M", "G", "GG", "3G", "4G", "5G", "6G"]
    justificativas = [
        "Acima de 60 anos",
        "Liberado pelo jurídico",
        "Liberado pela coordenação",
        "Liberado pelo presidente",
        "Erro de Sistema",
    ]
    equipes = Camisa.objects.values_list(
        "equipe", flat=True
    ).distinct()  # <-- opções de equipe

    if request.method == "POST":
        novo_tamanho = request.POST.get("tamcamisa", "").strip()
        situacao_raw = request.POST.get("situacao", None)
        justificativa = request.POST.get("justificativa", "").strip()
        observacao = request.POST.get("observacao", "").strip()
        nova_equipe = request.POST.get("equipe", "").strip()

        # validações mínimas
        if not novo_tamanho:
            messages.error(request, "Selecione um novo tamanho.")
            return render(
                request,
                "camisa/changecamisa.html",
                {
                    "camisa": camisa,
                    "tamanhos_camisa": tamanhos_camisa,
                    "justificativas": justificativas,
                    "equipes": equipes,
                },
            )

        if situacao_raw is None:
            messages.error(request, "Selecione a situação (APTO/INAPTO).")
            return render(
                request,
                "camisa/changecamisa.html",
                {
                    "camisa": camisa,
                    "tamanhos_camisa": tamanhos_camisa,
                    "justificativas": justificativas,
                    "equipes": equipes,
                },
            )

        if not nova_equipe:
            messages.error(request, "Selecione a equipe.")
            return render(
                request,
                "camisa/changecamisa.html",
                {
                    "camisa": camisa,
                    "tamanhos_camisa": tamanhos_camisa,
                    "justificativas": justificativas,
                    "equipes": equipes,
                },
            )

        nova_situacao = (
            True if str(situacao_raw) in ["1", "True", "true", "on"] else False
        )

        # Se não houve alteração, apenas avisa
        if (
            camisa.tamcamisa == novo_tamanho
            and camisa.situacao == nova_situacao
            and camisa.equipe == nova_equipe
        ):
            messages.info(
                request,
                "Nenhuma alteração detectada (tamanho, situação e equipe iguais aos atuais).",
            )
            return redirect("app:changecamisa", idcamisa=idcamisa)

        usuario = request.user if request.user.is_authenticated else None

        # cria log
        CamisaLog.objects.create(
            camisa=camisa,
            usuario=usuario,
            tamanho_antigo=camisa.tamcamisa,
            tamanho_novo=novo_tamanho,
            situacao_antiga="APTO" if camisa.situacao else "INAPTO",
            situacao_nova="APTO" if nova_situacao else "INAPTO",
            equipe_antiga=camisa.equipe,
            equipe_nova=nova_equipe,
            justificativa=justificativa,
            observacao=observacao,
            data_alteracao=timezone.now(),
        )

        # atualiza a camisa
        camisa.tamcamisa = novo_tamanho
        camisa.situacao = nova_situacao
        camisa.equipe = nova_equipe
        camisa.data = timezone.now()
        camisa.save()

        messages.success(
            request,
            f"Tamanho, situação e equipe da camisa do guarda {camisa.guarda.nome} atualizados com sucesso!",
        )
        return redirect("app:readcamisa")

    return render(
        request,
        "camisa/changecamisa.html",
        {
            "camisa": camisa,
            "tamanhos_camisa": tamanhos_camisa,
            "justificativas": justificativas,
            "equipes": equipes,
        },
    )


@group_required("super", "Direção")
def readcamisa(request):
    # =========================
    # Parâmetros da requisição
    # =========================
    query = request.GET.get("q", "").strip()
    ano = request.GET.get("ano", "").strip()
    equipe = request.GET.get("equipe", "").strip()
    recebido = request.GET.get("recebido", "").strip().lower()
    entregador_nome = request.GET.get("entregador", "").strip()

    per_page = request.GET.get("per_page", "10")
    page_number = request.GET.get("page")

    sort = request.GET.get("sort", "ano")
    direction = request.GET.get("dir", "desc")

    # =========================
    # Campos permitidos p/ ordenação
    # =========================
    sort_map = {
        "matricula": "guarda__matricula",
        "nome": "guarda__pessoa__nome",
        "ano": "ano",
        "equipe": "equipe",
        "data": "data",
        "entregador": "entregador__pessoa__nome",
        "tamanho": "tamcamisa",
    }

    if sort not in sort_map:
        sort = "ano"

    if direction not in ["asc", "desc"]:
        direction = "desc"

    # =========================
    # Query base otimizada
    # =========================
    camisas = Camisa.objects.select_related("guarda", "entregador")

    # =========================
    # Filtro: busca geral
    # =========================
    if query:
        filtros = Q(guarda__pessoa__nome__icontains=query) | Q(
            guarda__matricula__icontains=query
        )

        # tentativa de interpretar como data (DD/MM/AAAA)
        try:
            data_busca = datetime.strptime(query, "%d/%m/%Y").date()
            filtros |= Q(data__date=data_busca)
        except ValueError:
            pass

        camisas = camisas.filter(filtros)

    # =========================
    # Filtros específicos
    # =========================
    if ano:
        camisas = camisas.filter(ano=ano)

    if equipe:
        camisas = camisas.filter(equipe=equipe)

    if recebido == "sim":
        camisas = camisas.filter(recebido=True)

    elif recebido == "nao":
        camisas = camisas.filter(recebido=False, situacao=True)

    if entregador_nome:
        camisas = camisas.filter(entregador__pessoa__nome=entregador_nome)

    # =========================
    # Ordenação
    # =========================
    campo_ordenacao = sort_map[sort]

    if direction == "desc":
        campo_ordenacao = f"-{campo_ordenacao}"

    camisas = camisas.order_by(campo_ordenacao)

    # =========================
    # Paginação
    # =========================
    if per_page == "Todos":
        page_obj = camisas
    else:
        try:
            per_page = int(per_page)
        except ValueError:
            per_page = 10

        paginator = Paginator(camisas, per_page)
        page_obj = paginator.get_page(page_number)

    per_page_options = [10, 25, 50, 100, "Todos"]

    # =========================
    # Dados para filtros
    # =========================
    equipes_disponiveis = (
        Camisa.objects.values_list("equipe", flat=True).distinct().order_by("equipe")
    )

    entregadores_disponiveis = (
        Camisa.objects.filter(recebido=True)
        .values_list("entregador__pessoa__nome", flat=True)
        .distinct()
        .order_by("entregador__pessoa__nome")
    )

    # =========================
    # Contexto
    # =========================
    context = {
        "page_obj": page_obj,
        "query": query,
        "ano": ano,
        "equipe": equipe,
        "recebido": recebido,
        "entregador_nome": entregador_nome,
        "sort": sort,
        "dir": direction,
        "per_page": per_page,
        "per_page_options": per_page_options,
        "equipes_disponiveis": equipes_disponiveis,
        "entregadores_disponiveis": entregadores_disponiveis,
    }

    return render(request, "camisa/readcamisa.html", context)


@group_required("super")
def deletar_camisas_por_ano(request):
    # Pega todos os anos distintos no banco, ordenados decrescente
    anos = Camisa.objects.values_list("ano", flat=True).distinct().order_by("-ano")

    if request.method == "POST":
        ano = request.POST.get("ano")
        if ano:
            try:
                ano = int(ano)
                camisas = Camisa.objects.filter(ano=ano)
                if camisas.exists():
                    # Deleta logs relacionados
                    CamisaLog.objects.filter(camisa__in=camisas).delete()
                    # Deleta camisas
                    camisas.delete()
                    messages.success(
                        request,
                        f"Todas as camisas e logs do ano {ano} foram deletados!",
                    )
                else:
                    messages.info(
                        request, f"Não existem camisas cadastradas para o ano {ano}."
                    )
            except ValueError:
                messages.error(request, "Ano inválido.")
        else:
            messages.error(request, "Informe um ano.")
        return redirect("app:deletar_camisas_por_ano")

    return render(request, "camisa/deletar_por_ano.html", {"anos": anos})


@group_required("super", "Direção")
def camisa_entregue(request):
    # Filtros e parâmetros
    query = request.GET.get("q", "")
    ano = request.GET.get("ano", "")
    per_page = request.GET.get("per_page", 10)
    terceiro_only = request.GET.get("terceiro_only", "")

    try:
        per_page = int(per_page)
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Queryset base: apenas camisas já recebidas
    camisas_qs = Camisa.objects.filter(recebido=True).select_related(
        "guarda", "entregador"
    )

    # Filtro de busca
    if query:
        camisas_qs = camisas_qs.filter(
            Q(guarda__pessoa__nome__icontains=query) | Q(guarda__matricula__icontains=query)
        )

    # Filtro por ano
    if ano:
        try:
            ano_int = int(ano)
            camisas_qs = camisas_qs.filter(ano=ano_int)
        except ValueError:
            pass

    # Filtrar apenas casos em que o recebedor não é o próprio
    if terceiro_only:
        camisas_qs = camisas_qs.exclude(recebedor=F("guarda__pessoa__nome"))

    # Ordenação padrão (opcional)
    camisas_qs = camisas_qs.order_by("-ano", "guarda__pessoa__nome")

    # Paginação
    paginator = Paginator(camisas_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "camisa/camisa_entregue.html",
        {
            "page_obj": page_obj,
            "query": query,
            "ano": ano,
            "per_page": per_page,
            "terceiro_only": terceiro_only,
            "per_page_options": [5, 10, 20, 50],
        },
    )


@group_required("super", "Direção")
def createcamisa(request, guarda_id):
    guarda = get_object_or_404(Guarda, pk=guarda_id)
    criador = get_object_or_404(Guarda, matricula=request.user.matricula)

    if request.method == "POST":
        form = CamisaForm(request.POST, request.FILES)

        if form.is_valid():
            camisa = form.save(commit=False)

            camisa.guarda = guarda
            camisa.entregador = guarda
            camisa.criador = criador
            camisa.data = timezone.now()
            camisa.situacao = True
            camisa.recebido = False

            camisa.arquivo = None
            camisa.procuracao = None
            camisa.recebedor = None

            camisa.save()
            messages.success(request, "Camisa cadastrada com sucesso.")
            return redirect("app:readcamisa")

        else:
            # 🔴 Tratamento de erro de validação do form
            for campo, erros in form.errors.items():
                for erro in erros:
                    messages.error(request, f"Erro no campo '{campo}': {erro}")

    else:
        form = CamisaForm()

    return render(
        request,
        "camisa/createcamisa.html",
        {
            "form": form,
            "guarda": guarda,
        },
    )


@group_required("super")
def importacamisas(request):
    if request.method == "POST":
        ano = request.POST.get("ano")
        arquivo = request.FILES.get("arquivo")

        if not ano or len(ano) != 4 or not ano.isdigit():
            messages.error(request, "Digite um ano válido com 4 dígitos (ex: 2025).")
            return redirect("app:importacamisas")

        ano_int = int(ano)  # transforma "025" em 2025, "024" em 2024...

        if not arquivo:
            messages.error(request, "Selecione um arquivo XLSX para importar.")
            return redirect("app:importacamisas")

        try:
            wb = openpyxl.load_workbook(arquivo)
            sheet = wb.active

            # Apaga todas as camisas do ano informado
            Camisa.objects.filter(ano=ano_int).delete()

            count_guarda = 0
            count_camisa = 0

            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if i == 0:
                    # Ignora cabeçalho
                    continue

                mat = row[0]  # MAT
                nome = row[1]  # NOME
                equipe = row[2]  # EQ
                foto = row[3]  # FOTO (link externo)
                tamcamisa = row[4]  # CAM
                situacao = row[5]  # APTO MISSA
                turma = (
                    "1974"
                    if row[7] and str(row[7]).upper() == "ANTIGO"
                    else (row[7] if row[7] and str(row[7]).isdigit() else "0000")
                )  # TURMA ANO

                if not mat:
                    continue

                from guarda.models import Guarda, Pessoa
                
                # Atualiza ou cria guarda
                guarda = Guarda.objects.filter(matricula=mat).first()
                if guarda:
                    guarda.pessoa.nome = nome if nome else "NOME NÃO INFORMADO"
                    if foto:
                        guarda.pessoa.foto = foto
                    guarda.pessoa.save()
                    created = False
                else:
                    pessoa = Pessoa.objects.create(
                        nome=nome if nome else "NOME NÃO INFORMADO", 
                        foto=foto if foto else None
                    )
                    guarda = Guarda.objects.create(
                        matricula=mat, 
                        pessoa=pessoa, 
                        tipo="Mirim", 
                        status="Ativo"
                    )
                    created = True
                    
                if created:
                    count_guarda += 1

                # Converte situação
                situacao_bool = (
                    True if str(situacao).strip().upper() == "APTO" else False
                )

                # Cria camisa
                Camisa.objects.create(
                    idcamisa=int(
                        str(mat) + str(ano)
                    ),  # idcamisa = matricula+ano (ou ajusta se precisar)
                    ano=ano_int,
                    guarda=guarda,
                    equipe=equipe if equipe else "N/A",
                    situacao=situacao_bool,
                    tamcamisa=tamcamisa if tamcamisa else "N/A",
                    recebido=False,
                    arquivo=None,
                    recebedor=None,
                    entregador=guarda,  # se não tiver, bota ele mesmo
                    data=timezone.now().date(),
                )
                count_camisa += 1

            messages.success(
                request,
                f"Importação concluída: {count_guarda} guardas criados/atualizados, {count_camisa} camisas inseridas.",
            )
            return redirect("app:importacamisas")

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {str(e)}")
            return redirect("app:importacamisas")

    return render(request, "camisa/importacamisas.html")


@login_required()
def relatorio_geral(request):
    # ano selecionado
    ano = request.GET.get("ano") or None

    camisas_qs = Camisa.objects.filter(situacao=True)
    if ano:
        camisas_qs = camisas_qs.filter(ano=ano)

    anos = (
        Camisa.objects.filter(situacao=True)
        .values_list("ano", flat=True)
        .distinct()
        .order_by("ano")
    )

    # ordem de tamanhos
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

    # equipes presentes no queryset
    equipes = sorted(camisas_qs.values_list("equipe", flat=True).distinct())

    # inicializa tabelas e totais
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

    for equipe in equipes:
        fator = fator_equipes(equipe)
        for tam in ordem_tamanhos:
            qtd_base = camisas_qs.filter(equipe=equipe, tamcamisa=tam).count()
            total_aptos = qtd_base * fator
            if total_aptos == 0:
                continue

            total_entregues = (
                camisas_qs.filter(equipe=equipe, tamcamisa=tam, recebido=True).count()
                * fator
            )
            a_entregar = total_aptos - total_entregues

            # adicionar linha na tabela
            tabela_dados.append(
                {
                    "equipe": equipe,
                    "tamanho": tam,
                    "entregues": total_entregues,
                    "a_entregar": a_entregar,
                }
            )

            # acumula dados para gráficos
            entregues_por_equipe[equipe] = (
                entregues_por_equipe.get(equipe, 0) + total_entregues
            )
            entregues_por_tamanho[tam] = (
                entregues_por_tamanho.get(tam, 0) + total_entregues
            )
            entregues_por_equipe_tamanho.setdefault(equipe, {})[tam] = total_entregues

            a_entregar_por_equipe[equipe] = (
                a_entregar_por_equipe.get(equipe, 0) + a_entregar
            )
            a_entregar_por_tamanho[tam] = (
                a_entregar_por_tamanho.get(tam, 0) + a_entregar
            )
            a_entregar_por_equipe_tamanho.setdefault(equipe, {})[tam] = a_entregar

            totais_por_equipe[equipe] = totais_por_equipe.get(equipe, 0) + total_aptos
            totais_por_tamanho[tam] = totais_por_tamanho.get(tam, 0) + total_aptos
            totais_por_equipe_tamanho.setdefault(equipe, {})[tam] = total_aptos

    # linha TOTAL
    total_entregues_all = sum(row["entregues"] for row in tabela_dados)
    total_a_entregar_all = sum(row["a_entregar"] for row in tabela_dados)
    tabela_dados.append(
        {
            "equipe": "TOTAL",
            "tamanho": "-",
            "entregues": total_entregues_all,
            "a_entregar": total_a_entregar_all,
        }
    )

    context = {
        "tabela_dados": tabela_dados,
        "entregues_por_equipe": json.dumps(entregues_por_equipe),
        "entregues_por_tamanho": json.dumps(entregues_por_tamanho),
        "entregues_por_equipe_tamanho": json.dumps(entregues_por_equipe_tamanho),
        "a_entregar_por_equipe": json.dumps(a_entregar_por_equipe),
        "a_entregar_por_tamanho": json.dumps(a_entregar_por_tamanho),
        "a_entregar_por_equipe_tamanho": json.dumps(a_entregar_por_equipe_tamanho),
        "totais_por_equipe": json.dumps(totais_por_equipe),
        "totais_por_tamanho": json.dumps(totais_por_tamanho),
        "totais_por_equipe_tamanho": json.dumps(totais_por_equipe_tamanho),
        "anos": anos,
        "ano_selecionado": ano,
        "ordem_tamanhos": ordem_tamanhos,
    }
    return render(request, "camisa/relatorio_geral.html", context)


@login_required()
def relatorio_por_equipe(request):
    anos_disponiveis = (
        Camisa.objects.filter(situacao=True)
        .values_list("ano", flat=True)
        .distinct()
        .order_by("ano")
    )
    ano = request.GET.get("ano")
    dias_selecionados = request.GET.getlist("data")

    camisas_qs = Camisa.objects.filter(situacao=True)
    if ano:
        camisas_qs = camisas_qs.filter(ano=ano)

    dias_entregas = sorted(
        set(camisa.data.date() for camisa in camisas_qs if camisa.data)
    )

    if dias_selecionados:
        selected_dates = [
            datetime.strptime(s, "%Y-%m-%d").date() for s in dias_selecionados
        ]
        camisas_qs = camisas_qs.filter(data__date__in=selected_dates)

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
    equipes = sorted(camisas_qs.values_list("equipe", flat=True).distinct())

    tabela_camisas = OrderedDict()
    total_geral_entregues = 0
    total_geral_pendente = 0
    total_geral_aptos = 0

    for tam in ordem_tamanhos:
        equipes_corrigidas = []
        total_entregues_tam = 0
        total_pendente_tam = 0

        for equipe in equipes:
            qtd_base = camisas_qs.filter(equipe=equipe, tamcamisa=tam).count()
            if qtd_base == 0:
                continue

            fator = fator_equipes(equipe)

            total_aptos = qtd_base * fator
            entregues_count = camisas_qs.filter(
                equipe=equipe, tamcamisa=tam, recebido=True
            ).count()
            total_entregues = entregues_count * fator
            pendentes = total_aptos - total_entregues

            equipes_corrigidas.append(
                {
                    "equipe": equipe,
                    "qtd_base": qtd_base,  # debug opcional
                    "fator": fator,  # debug opcional
                    "entregues": total_entregues,
                    "a_entregar": pendentes,
                }
            )

            total_entregues_tam += total_entregues
            total_pendente_tam += pendentes
            total_geral_aptos += total_aptos

        if equipes_corrigidas:
            tabela_camisas[tam] = {
                "equipes": equipes_corrigidas,
                "total_entregues": total_entregues_tam,
                "total_pendente": total_pendente_tam,
            }
            total_geral_entregues += total_entregues_tam
            total_geral_pendente += total_pendente_tam

    context = {
        "anos_disponiveis": anos_disponiveis,
        "ano_selecionado": ano,
        "dias_entregas": dias_entregas,
        "dias_selecionados": dias_selecionados,
        "tabela_camisas": tabela_camisas,
        "total_geral_entregues": total_geral_entregues,
        "total_geral_pendente": total_geral_pendente,
        "total_geral_aptos": total_geral_aptos,  # útil para checagem (deve bater com 4416)
    }
    return render(request, "camisa/relatorio_por_equipe.html", context)


@login_required
def relatorio_por_tamanho(request):
    # --- Filtros ---
    ano_selecionado = request.GET.get("ano")
    dias_selecionados = request.GET.getlist("data")

    # Lista de anos disponíveis
    anos = Camisa.objects.values_list("ano", flat=True).distinct().order_by("ano")

    # Lista de dias de entrega (só a data, sem hora)
    dias_entregas = (
        Camisa.objects.annotate(so_data=TruncDate("data"))
        .values_list("so_data", flat=True)
        .distinct()
        .order_by("so_data")
    )

    # Query base: somente camisas aptas
    qs = Camisa.objects.filter(situacao=True)

    if ano_selecionado:
        qs = qs.filter(ano=ano_selecionado)

    if dias_selecionados:
        qs = qs.filter(data__date__in=dias_selecionados)

    # --- Consulta agrupada por equipe e tamanho ---
    dados = (
        qs.values("equipe", "tamcamisa")
        .annotate(
            entregues=Count("id", filter=Q(recebido=True)),
            a_entregar=Count("id", filter=Q(recebido=False)),
        )
        .order_by("equipe", "tamcamisa")
    )

    # --- Ordem personalizada dos tamanhos ---
    ordem_tamanhos = [
        "PP",
        "P",
        "M",
        "G",
        "GG",
        "3G",
        "4G",
        "5G",
        "6G",
        "XG",
        "UN",
        "ESPECIAL",
    ]

    # --- Reorganiza dados em dict por equipe e aplica fator ---
    tabela_por_equipe = {}
    for d in dados:
        equipe = d["equipe"]
        fator = fator_equipes(equipe)

        if equipe not in tabela_por_equipe:
            tabela_por_equipe[equipe] = {
                "total_entregues": 0,
                "total_pendente": 0,
                "tamanhos": [],
            }

        entregues_fator = d["entregues"] * fator
        pendente_fator = d["a_entregar"] * fator

        tabela_por_equipe[equipe]["tamanhos"].append(
            {
                "tamcamisa": d["tamcamisa"],
                "entregues": entregues_fator,
                "a_entregar": pendente_fator,
            }
        )
        tabela_por_equipe[equipe]["total_entregues"] += entregues_fator
        tabela_por_equipe[equipe]["total_pendente"] += pendente_fator

    # --- Ordena tamanhos dentro de cada equipe ---
    for equipe, info in tabela_por_equipe.items():
        info["tamanhos"].sort(
            key=lambda x: (
                ordem_tamanhos.index(x["tamcamisa"])
                if x["tamcamisa"] in ordem_tamanhos
                else 99
            )
        )

    # --- Totais gerais com fator ---
    total_geral = {
        "total_entregues": sum(
            e["total_entregues"] for e in tabela_por_equipe.values()
        ),
        "total_pendente": sum(e["total_pendente"] for e in tabela_por_equipe.values()),
    }

    context = {
        "anos": anos,
        "ano_selecionado": ano_selecionado,
        "dias_entregas": dias_entregas,
        "dias_selecionados": dias_selecionados,
        "tabela_camisas": tabela_por_equipe,
        "total_geral_entregues": total_geral["total_entregues"],
        "total_geral_pendente": total_geral["total_pendente"],
    }
    return render(request, "camisa/relatorio_por_tamanho.html", context)
