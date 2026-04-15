import re
import json
import base64
from datetime import datetime
from collections import OrderedDict

import numpy as np
import cv2
import faiss
import face_recognition
import openpyxl

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q, OuterRef, Subquery, Count, Sum, Max
from django.db.models.functions import TruncDate
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import GuardaForm, GuardaGroupForm, ForceChangePasswordForm, CamisaForm
from .models import Guarda, Camisa, CamisaLog, GuardaApoio, CamisaGuardaApoio
from .faiss_index import face_index



# Create your views here.
@login_required
def home(request):
    return render(request, 'index.html')

def group_required(*group_names):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect("app:home")
        return _wrapped_view
    return decorator

@group_required('super', 'Direção')
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
            if 'foto' in form.changed_data and guarda.foto:
                imagem = face_recognition.load_image_file(guarda.foto.path)
                rostos = face_recognition.face_encodings(imagem)
                if rostos:
                    guarda.encoding = np.array(rostos[0], dtype=np.float32).tobytes()

            guarda.save()
            face_index.load_index()  # atualiza FAISS
            messages.success(request, f"Guarda {guarda.nome} salvo com sucesso!")
            return redirect('app:readguarda')

    return render(request, 'createguarda.html', {'form': form})

@group_required('super','Direção')
def camisa_entregue(request):
    # Filtros e parâmetros
    query = request.GET.get('q', '')
    ano = request.GET.get('ano', '')
    per_page = request.GET.get('per_page', 10)
    terceiro_only = request.GET.get('terceiro_only', '')

    try:
        per_page = int(per_page)
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Queryset base: apenas camisas já recebidas
    camisas_qs = Camisa.objects.filter(recebido=True).select_related('guarda', 'entregador')

    # Filtro de busca
    if query:
        camisas_qs = camisas_qs.filter(
            Q(guarda__nome__icontains=query) |
            Q(guarda__matricula__icontains=query)
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
        camisas_qs = camisas_qs.exclude(recebedor=F('guarda__nome'))

    # Ordenação padrão (opcional)
    camisas_qs = camisas_qs.order_by('-ano', 'guarda__nome')

    # Paginação
    paginator = Paginator(camisas_qs, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'camisa_entregue.html', {
        'page_obj': page_obj,
        'query': query,
        'ano': ano,
        'per_page': per_page,
        'terceiro_only': terceiro_only,
        'per_page_options': [5, 10, 20, 50],
    })

@group_required('super','Direção')
def readguarda(request):
    search = request.GET.get('search', '')
    per_page = request.GET.get('per_page', 10)
    sort = request.GET.get('sort', 'nome')
    direction = request.GET.get('direction', 'asc')

    try:
        per_page = int(per_page)
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Subquery para a camisa mais recente
    camisas_recents = Camisa.objects.filter(guarda=OuterRef('pk')).order_by('-ano')

    # Queryset base
    guardas_qs = Guarda.objects.all().annotate(
        equipe_recente=Subquery(camisas_recents.values('equipe')[:1]),
        tamcamisa_recente=Subquery(camisas_recents.values('tamcamisa')[:1])
    )

    # Filtro de busca
    if search:
        guardas_qs = guardas_qs.filter(
            Q(nome__icontains=search) |
            Q(matricula__icontains=search) |
            Q(cpf__icontains=search)
        )

    # Converte para lista para manipular permissões
    guardas_list = list(guardas_qs)

    for g in guardas_list:
        grupos = list(g.groups.values_list('name', flat=True))
        g.grupos = grupos
        g.first_group_name = grupos[0] if grupos else ''

    # Ordenação
    valid_sorts = {
        'matricula': lambda x: x.matricula or '',
        'nome': lambda x: x.nome or '',
        'cpf': lambda x: x.cpf or '',
        'equipe_recente': lambda x: x.equipe_recente or '',
        'tamcamisa_recente': lambda x: x.tamcamisa_recente or '',
        'grupos': lambda x: x.first_group_name
    }
    sort_func = valid_sorts.get(sort, valid_sorts['nome'])
    reverse = direction == 'desc'
    guardas_list.sort(key=sort_func, reverse=reverse)

    # Paginação
    paginator = Paginator(guardas_list, per_page)
    page_number = request.GET.get('page')
    guardas_page = paginator.get_page(page_number)

    return render(request, 'readguarda.html', {
        'guardas': guardas_page,
        'request': request,
        'sort': sort,
        'direction': direction
    })

@group_required('super','Direção')
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
                messages.error(request, "A senha deve conter pelo menos uma letra maiúscula.")
            elif not re.search(r"[a-z]", senha):
                messages.error(request, "A senha deve conter pelo menos uma letra minúscula.")
            elif not re.search(r"[0-9]", senha):
                messages.error(request, "A senha deve conter pelo menos um número.")
            elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
                messages.error(request, "A senha deve conter pelo menos um caractere especial.")
            else:
                # Tudo ok, salvar senha
                guarda.set_password(senha)
                guarda.must_change_password = True
                guarda.save()
                messages.success(request, f"Senha cadastrada com sucesso para {guarda.nome}!")
                return redirect("app:readguarda")

    return render(request, "passwordguarda.html", {"guarda": guarda})

@login_required
def findcamisa(request):
    anos = Camisa.objects.filter(situacao=True).values_list("ano", flat=True).distinct()
    error = None

    # Últimas 20 camisas entregues
    ultimas_camisas = Camisa.objects.filter(recebido=True).order_by('-data')[:20]

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
            return render(request, "findcamisa.html", {'anos': anos, 'error': error, 'ultimas_camisas': ultimas_camisas})

        try:
            camisa = Camisa.objects.get(guarda=guarda, ano=ano)
        except Camisa.DoesNotExist:
            error = f"Nenhuma camisa encontrada para o guarda {guarda.nome} no ano de {ano}."
            return render(request, "findcamisa.html", {'anos': anos, 'error': error, 'ultimas_camisas': ultimas_camisas})

        mesma_equipe = camisa.equipe == camisa_guarda_logado.equipe
        grupo_entrega_geral = request.user.groups.filter(name='Entregador_geral').exists()
        print(grupo_entrega_geral)

        if not mesma_equipe and not grupo_entrega_geral:
            error = (
                f"O usuário {guarda_logado.nome} não pode entregar camisa "
                f"da equipe {camisa.equipe}."
            )
            return render(request, "findcamisa.html", {
                'anos': anos,
                'error': error,
                'ultimas_camisas': ultimas_camisas
            })

        if not camisa.situacao:  # INAPTO
            error = f'O guarda {guarda.nome} no ano de {ano} está INAPTO!'
        elif camisa.recebido:  # RECEBIDO
            error = f'A camisa do guarda {guarda.nome} no ano de {ano} já foi entregue para {camisa.recebedor} por {camisa.entregador}.'
        else:
            request.session['guarda_id'] = guarda.idguarda
            request.session['camisa_id'] = camisa.id
            return redirect('app:takecamisa')

    return render(request, "findcamisa.html", {
        'anos': anos,
        'error': error,
        'ultimas_camisas': ultimas_camisas
    })

@login_required
def takecamisa(request):
    guarda_id = request.session.pop('guarda_id', None)
    camisa_id = request.session.pop('camisa_id', None)
    if not guarda_id or not camisa_id:
        return redirect('app:findcamisa')  # se não houver dados
    # buscar objetos no banco
    guarda = Guarda.objects.get(idguarda=guarda_id)
    print(camisa_id)
    camisa = Camisa.objects.get(id=camisa_id)
    return render(request, 'takecamisa.html', {'guarda': guarda, 'camisa': camisa})

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
                messages.error(request, "Informe o nome do recebedor ou marque 'É o próprio'.")
                return redirect("app:takecamisa")

            # Exigir procuração se não for o próprio
            #if not procuracao:
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

        messages.success(request, f"A camisa do guarda {guarda.nome} foi entregue com sucesso para {recebedor}!")
        return redirect("app:takecamisa")

    return redirect("app:takecamisa")

@group_required('super','Direção')
def changecamisa(request, idcamisa):
    try:
        camisa = get_object_or_404(Camisa, id=idcamisa)
    except Http404:
        camisa = get_object_or_404(Camisa, id=idcamisa)

    tamanhos_camisa = ['PP', 'P', 'M', 'G', 'GG', '3G', '4G', '5G', '6G']
    justificativas = [
        "Acima de 60 anos",
        "Liberado pelo jurídico",
        "Liberado pela coordenação",
        "Liberado pelo presidente",
        "Erro de Sistema"
    ]
    equipes = Camisa.objects.values_list('equipe', flat=True).distinct()  # <-- opções de equipe

    if request.method == "POST":
        novo_tamanho = request.POST.get("tamcamisa", "").strip()
        situacao_raw = request.POST.get("situacao", None)
        justificativa = request.POST.get("justificativa", "").strip()
        observacao = request.POST.get("observacao", "").strip()
        nova_equipe = request.POST.get("equipe", "").strip()

        # validações mínimas
        if not novo_tamanho:
            messages.error(request, "Selecione um novo tamanho.")
            return render(request, 'changecamisa.html', {
                'camisa': camisa,
                'tamanhos_camisa': tamanhos_camisa,
                'justificativas': justificativas,
                'equipes': equipes
            })

        if situacao_raw is None:
            messages.error(request, "Selecione a situação (APTO/INAPTO).")
            return render(request, 'changecamisa.html', {
                'camisa': camisa,
                'tamanhos_camisa': tamanhos_camisa,
                'justificativas': justificativas,
                'equipes': equipes
            })

        if not nova_equipe:
            messages.error(request, "Selecione a equipe.")
            return render(request, 'changecamisa.html', {
                'camisa': camisa,
                'tamanhos_camisa': tamanhos_camisa,
                'justificativas': justificativas,
                'equipes': equipes
            })

        nova_situacao = True if str(situacao_raw) in ['1', 'True', 'true', 'on'] else False

        # Se não houve alteração, apenas avisa
        if (
                camisa.tamcamisa == novo_tamanho and
                camisa.situacao == nova_situacao and
                camisa.equipe == nova_equipe
        ):
            messages.info(request, "Nenhuma alteração detectada (tamanho, situação e equipe iguais aos atuais).")
            return redirect('app:changecamisa', idcamisa=idcamisa)

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
            data_alteracao=timezone.now()
        )

        # atualiza a camisa
        camisa.tamcamisa = novo_tamanho
        camisa.situacao = nova_situacao
        camisa.equipe = nova_equipe
        camisa.data = timezone.now()
        camisa.save()

        messages.success(request, f"Tamanho, situação e equipe da camisa do guarda {camisa.guarda.nome} atualizados com sucesso!")
        return redirect('app:readcamisa')

    return render(request, 'changecamisa.html', {
        'camisa': camisa,
        'tamanhos_camisa': tamanhos_camisa,
        'justificativas': justificativas,
        'equipes': equipes
    })

@group_required('super', 'Direção')
def readcamisa(request):
    # =========================
    # Parâmetros da requisição
    # =========================
    query = request.GET.get('q', '').strip()
    ano = request.GET.get('ano', '').strip()
    equipe = request.GET.get('equipe', '').strip()
    recebido = request.GET.get('recebido', '').strip().lower()
    entregador_nome = request.GET.get('entregador', '').strip()

    per_page = request.GET.get('per_page', '10')
    page_number = request.GET.get('page')

    sort = request.GET.get('sort', 'ano')
    direction = request.GET.get('dir', 'desc')

    # =========================
    # Campos permitidos p/ ordenação
    # =========================
    sort_map = {
        'matricula': 'guarda__matricula',
        'nome': 'guarda__nome',
        'ano': 'ano',
        'equipe': 'equipe',
        'data': 'data',
        'entregador': 'entregador__nome',
        'tamanho': 'tamcamisa',
    }

    if sort not in sort_map:
        sort = 'ano'

    if direction not in ['asc', 'desc']:
        direction = 'desc'

    # =========================
    # Query base otimizada
    # =========================
    camisas = Camisa.objects.select_related(
        'guarda',
        'entregador'
    )

    # =========================
    # Filtro: busca geral
    # =========================
    if query:
        filtros = Q(
            guarda__nome__icontains=query
        ) | Q(
            guarda__matricula__icontains=query
        )

        # tentativa de interpretar como data (DD/MM/AAAA)
        try:
            data_busca = datetime.strptime(query, '%d/%m/%Y').date()
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

    if recebido == 'sim':
        camisas = camisas.filter(recebido=True)

    elif recebido == 'nao':
        camisas = camisas.filter(recebido=False, situacao=True)

    if entregador_nome:
        camisas = camisas.filter(entregador__nome=entregador_nome)

    # =========================
    # Ordenação
    # =========================
    campo_ordenacao = sort_map[sort]

    if direction == 'desc':
        campo_ordenacao = f'-{campo_ordenacao}'

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
        Camisa.objects
        .values_list('equipe', flat=True)
        .distinct()
        .order_by('equipe')
    )

    entregadores_disponiveis = (
        Camisa.objects
        .filter(recebido=True)
        .values_list('entregador__nome', flat=True)
        .distinct()
        .order_by('entregador__nome')
    )

    # =========================
    # Contexto
    # =========================
    context = {
        'page_obj': page_obj,
        'query': query,
        'ano': ano,
        'equipe': equipe,
        'recebido': recebido,
        'entregador_nome': entregador_nome,

        'sort': sort,
        'dir': direction,

        'per_page': per_page,
        'per_page_options': per_page_options,

        'equipes_disponiveis': equipes_disponiveis,
        'entregadores_disponiveis': entregadores_disponiveis,
    }

    return render(request, 'readcamisa.html', context)

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

@login_required()
def relatorios(request):
    # ano selecionado
    ano = request.GET.get("ano") or None

    camisas_qs = Camisa.objects.filter(situacao=True)
    if ano:
        camisas_qs = camisas_qs.filter(ano=ano)

    anos = Camisa.objects.filter(situacao=True).values_list("ano", flat=True).distinct().order_by("ano")

    # ordem de tamanhos
    ordem_tamanhos = ['PP','P','M','G','GG','XG','XGG','3G','4G','5G','6G','ESPECIAL']

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

            total_entregues = camisas_qs.filter(equipe=equipe, tamcamisa=tam, recebido=True).count() * fator
            a_entregar = total_aptos - total_entregues

            # adicionar linha na tabela
            tabela_dados.append({
                "equipe": equipe,
                "tamanho": tam,
                "entregues": total_entregues,
                "a_entregar": a_entregar
            })

            # acumula dados para gráficos
            entregues_por_equipe[equipe] = entregues_por_equipe.get(equipe,0) + total_entregues
            entregues_por_tamanho[tam] = entregues_por_tamanho.get(tam,0) + total_entregues
            entregues_por_equipe_tamanho.setdefault(equipe,{})[tam] = total_entregues

            a_entregar_por_equipe[equipe] = a_entregar_por_equipe.get(equipe,0) + a_entregar
            a_entregar_por_tamanho[tam] = a_entregar_por_tamanho.get(tam,0) + a_entregar
            a_entregar_por_equipe_tamanho.setdefault(equipe,{})[tam] = a_entregar

            totais_por_equipe[equipe] = totais_por_equipe.get(equipe,0) + total_aptos
            totais_por_tamanho[tam] = totais_por_tamanho.get(tam,0) + total_aptos
            totais_por_equipe_tamanho.setdefault(equipe,{})[tam] = total_aptos

    # linha TOTAL
    total_entregues_all = sum(row["entregues"] for row in tabela_dados)
    total_a_entregar_all = sum(row["a_entregar"] for row in tabela_dados)
    tabela_dados.append({
        "equipe": "TOTAL",
        "tamanho": "-",
        "entregues": total_entregues_all,
        "a_entregar": total_a_entregar_all
    })

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
    return render(request, "relatorios.html", context)

@login_required()
def relatorio_barras(request):
    ano = request.GET.get('ano')
    if not ano:
        ano = Camisa.objects.aggregate(Max('ano'))['ano__max']

    # Pega todos os anos distintos disponíveis
    anos_disponiveis = Camisa.objects.filter(situacao=True).values_list("ano", flat=True).distinct().order_by('ano')

    # Ano padrão
    if not ano and anos_disponiveis:
        ano = anos_disponiveis[0]

    camisas_aptas = Camisa.objects.filter(situacao=True, ano=ano)

    equipes = sorted(camisas_aptas.values_list('equipe', flat=True).distinct())
    tamanhos_ordem = ['PP','P','M','G','GG','XG','XGG','3G','4G','5G','6G','ESPECIAL']

    dados_por_equipe = {}

    for equipe in equipes:
        dados_por_equipe[equipe] = {}
        camisas_equipe = camisas_aptas.filter(equipe=equipe)
        for tamanho in tamanhos_ordem:
            total = camisas_equipe.filter(tamcamisa=tamanho).count()
            if total > 0:
                entregues = camisas_equipe.filter(tamcamisa=tamanho, recebido=True).count()
                a_entregar = total - entregues
                dados_por_equipe[equipe][tamanho] = {
                    'entregues': entregues,
                    'a_entregar': a_entregar
                }

    context = {
        'ano': ano,
        'anos_disponiveis': anos_disponiveis,
        'equipes': equipes,
        'tamanhos_ordem': tamanhos_ordem,
        'dados_por_equipe': json.dumps(dados_por_equipe),
    }
    return render(request, 'relatorio_barras.html', context)

@login_required()
def relatorio2(request):
    if request.method == "GET":
        ano = request.GET.get('ano')
    if not ano:
        ano = Camisa.objects.aggregate(Max('ano'))['ano__max']
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

    ordem_tamanhos = ['PP','P','M','G','GG','XG','XGG','3G','4G','5G','6G','ESPECIAL']

    for equipe in equipes:
        for tamanho in tamanhos:
            total_aptos = camisas_aptas.filter(equipe=equipe, tamcamisa=tamanho).count()
            total_entregues = camisas_aptas.filter(equipe=equipe, tamcamisa=tamanho, recebido=True).count()
            a_entregar = total_aptos - total_entregues

            if total_aptos > 0:
                tabela_dados.append({
                    "equipe": equipe,
                    "tamanho": tamanho,
                    "entregues": total_entregues,
                    "a_entregar": a_entregar
                })

                # Entregues
                entregues_por_equipe[equipe] = entregues_por_equipe.get(equipe, 0) + total_entregues
                entregues_por_tamanho[tamanho] = entregues_por_tamanho.get(tamanho, 0) + total_entregues
                entregues_por_equipe_tamanho.setdefault(equipe, {})[tamanho] = total_entregues

                # A entregar
                a_entregar_por_equipe[equipe] = a_entregar_por_equipe.get(equipe, 0) + a_entregar
                a_entregar_por_tamanho[tamanho] = a_entregar_por_tamanho.get(tamanho, 0) + a_entregar
                a_entregar_por_equipe_tamanho.setdefault(equipe, {})[tamanho] = a_entregar

                # Totais
                totais_por_equipe[equipe] = totais_por_equipe.get(equipe, 0) + total_aptos
                totais_por_tamanho[tamanho] = totais_por_tamanho.get(tamanho, 0) + total_aptos
                totais_por_equipe_tamanho.setdefault(equipe, {})[tamanho] = total_aptos

    # Adicionar linha de totais na tabela
    total_entregues_all = sum([row["entregues"] for row in tabela_dados])
    total_a_entregar_all = sum([row["a_entregar"] for row in tabela_dados])
    tabela_dados.append({
        "equipe": "TOTAL",
        "tamanho": "-",
        "entregues": total_entregues_all,
        "a_entregar": total_a_entregar_all
    })

    # Ordenação: por equipe (alfabética), e por tamanho na ordem definida
    tabela_dados = sorted(
        tabela_dados,
        key=lambda x: (
            x["equipe"] if x["equipe"] != "TOTAL" else "ZZZZ",  # TOTAL vai pro fim
            ordem_tamanhos.index(x["tamanho"]) if x["tamanho"] in ordem_tamanhos else 999
        )
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
        'anos': anos,
    }
    return render(request, "relatorio2.html", context)

@login_required()
def relatorio_entregas(request):
    anos_disponiveis = Camisa.objects.values_list('ano', flat=True).distinct().order_by('ano')
    ano = request.GET.get('ano')
    if not ano:
        ano = Camisa.objects.aggregate(Max('ano'))['ano__max']
    dias_selecionados = request.GET.getlist('data')  # multi-select

    labels = []
    data = []
    tabela_camisas = OrderedDict()
    total_geral = 0

    # Apenas entregas realizadas
    camisas_qs = Camisa.objects.filter(recebido=True)

    if ano:
        camisas_qs = camisas_qs.filter(ano=ano)

    # Extrai apenas a parte da data
    camisas_qs = camisas_qs.annotate(dia=TruncDate('data'))

    # Lista de dias únicos
    dias_entregas = camisas_qs.values_list('dia', flat=True).distinct().order_by('dia')

    if dias_selecionados:
        camisas_qs = camisas_qs.filter(dia__in=dias_selecionados)

    if camisas_qs.exists():
        # Gráfico - entregadores
        guardas = Guarda.objects.annotate(
            qtd=Count('camisas_entregues', filter=Q(camisas_entregues__in=camisas_qs))
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
        ordem_tamanhos = ['PP','P','M','G','GG','XG','XGG','3G','4G','5G','6G','ESPECIAL']
        for tam in ordem_tamanhos:
            qs_tam = camisas_qs.filter(tamcamisa=tam)
            if qs_tam.exists():
                equipes = qs_tam.values('equipe').annotate(qtd=Count('id')).order_by('equipe')

                equipes_corrigidas = []
                total_por_tam = 0
                for e in equipes:
                    qtd_corrigida = e['qtd'] #* fator_equipes(e['equipe'])
                    equipes_corrigidas.append({
                        'equipe': e['equipe'],
                        'qtd': qtd_corrigida
                    })
                    total_por_tam += qtd_corrigida

                tabela_camisas[tam] = {
                    'equipes': equipes_corrigidas,
                    'total': total_por_tam
                }
                total_geral += total_por_tam

    context = {
        'anos_disponiveis': anos_disponiveis,
        'ano_selecionado': ano,
        'dias_entregas': dias_entregas,
        'dias_selecionados': dias_selecionados,
        'labels': labels,
        'data': data,
        'tabela_camisas': tabela_camisas,
        'total_geral': total_geral,
    }

    return render(request, 'relatorio_entregas.html', context)

@login_required()
def relatorio_camisas(request):
    anos_disponiveis = Camisa.objects.filter(situacao=True).values_list('ano', flat=True).distinct().order_by('ano')
    ano = request.GET.get('ano')
    dias_selecionados = request.GET.getlist('data')

    camisas_qs = Camisa.objects.filter(situacao=True)
    if ano:
        camisas_qs = camisas_qs.filter(ano=ano)

    dias_entregas = sorted(set(camisa.data.date() for camisa in camisas_qs if camisa.data))

    if dias_selecionados:
        selected_dates = [datetime.strptime(s, '%Y-%m-%d').date() for s in dias_selecionados]
        camisas_qs = camisas_qs.filter(data__date__in=selected_dates)

    ordem_tamanhos = ['PP','P','M','G','GG','XG','XGG','3G','4G','5G','6G','ESPECIAL']
    equipes = sorted(camisas_qs.values_list('equipe', flat=True).distinct())

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
            entregues_count = camisas_qs.filter(equipe=equipe, tamcamisa=tam, recebido=True).count()
            total_entregues = entregues_count * fator
            pendentes = total_aptos - total_entregues

            equipes_corrigidas.append({
                'equipe': equipe,
                'qtd_base': qtd_base,   # debug opcional
                'fator': fator,         # debug opcional
                'entregues': total_entregues,
                'a_entregar': pendentes
            })

            total_entregues_tam += total_entregues
            total_pendente_tam += pendentes
            total_geral_aptos += total_aptos

        if equipes_corrigidas:
            tabela_camisas[tam] = {
                'equipes': equipes_corrigidas,
                'total_entregues': total_entregues_tam,
                'total_pendente': total_pendente_tam
            }
            total_geral_entregues += total_entregues_tam
            total_geral_pendente += total_pendente_tam

    context = {
        'anos_disponiveis': anos_disponiveis,
        'ano_selecionado': ano,
        'dias_entregas': dias_entregas,
        'dias_selecionados': dias_selecionados,
        'tabela_camisas': tabela_camisas,
        'total_geral_entregues': total_geral_entregues,
        'total_geral_pendente': total_geral_pendente,
        'total_geral_aptos': total_geral_aptos,  # útil para checagem (deve bater com 4416)
    }
    return render(request, 'relatorio_camisas.html', context)

@group_required('super','Direção')
def permissoes(request, idguarda):
    guarda = get_object_or_404(Guarda, idguarda=idguarda)

    if request.method == "POST":
        form = GuardaGroupForm(request.POST, instance=guarda)
        if form.is_valid():
            if request.POST.get('reset_senha'):
                guarda.set_password("Guarda2025@")
                guarda.must_change_password = True
                guarda.save()
                form.save()
                messages.success(request, f"Permissões atualizadas para {guarda.nome} e Senha resetada para: Guarda2025@")
            else:
                form.save()
                messages.success(request, f"Permissões atualizadas para {guarda.nome}.")
            return redirect('app:readguarda')  # ou outra página de listagem
    else:
        form = GuardaGroupForm(instance=guarda)

    return render(request, 'permissoes.html', {'form': form, 'guarda': guarda})

@group_required('super')
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

                mat = row[0]   # MAT
                nome = row[1]  # NOME
                equipe = row[2]  # EQ
                foto = row[3]  # FOTO (link externo)
                tamcamisa = row[4]  # CAM
                situacao = row[5]  # APTO MISSA
                turma = "1974" if row[7] and str(row[7]).upper() == "ANTIGO" else (row[7] if row[7] and str(row[7]).isdigit() else "0000")  # TURMA ANO

                if not mat:
                    continue

                # Atualiza ou cria guarda
                guarda, created = Guarda.objects.update_or_create(
                    matricula=mat,
                    defaults={
                        "nome": nome if nome else "NOME NÃO INFORMADO",
                        "turma":turma,
                        "nascimento": None,
                        "foto": foto if foto else None,
                    }
                )
                if created:
                    count_guarda += 1

                # Converte situação
                situacao_bool = True if str(situacao).strip().upper() == "APTO" else False

                # Cria camisa
                Camisa.objects.create(
                    idcamisa=int(str(mat) + str(ano)),  # idcamisa = matricula+ano (ou ajusta se precisar)
                    ano=ano_int,
                    guarda=guarda,
                    equipe=equipe if equipe else "N/A",
                    situacao=situacao_bool,
                    tamcamisa=tamcamisa if tamcamisa else "N/A",
                    recebido=False,
                    arquivo=None,
                    recebedor=None,
                    entregador=guarda,  # se não tiver, bota ele mesmo
                    data=timezone.now().date()
                )
                count_camisa += 1

            messages.success(request, f"Importação concluída: {count_guarda} guardas criados/atualizados, {count_camisa} camisas inseridas.")
            return redirect("app:importacamisas")

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {str(e)}")
            return redirect("app:importacamisas")

    return render(request, "importacamisas.html")

@group_required('super')
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
                nome = row[1]       # CAD_NOME
                rg = row[3]         # CAD_RG
                cpf = row[4]        # CAD_CPF
                estado_civil = str(row[5]).strip()  # CAD_EST_CIVIL
                nascimento_valor = row[6]  # CAD_NASC
                try:
                    nascimento = datetime.strptime(str(nascimento_valor).split(" ")[0], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    nascimento = None
                telefone = row[7]   # CAD_TEL_RES
                celular = row[8]    # CAD_TEL_CEL
                tel_comercial = row[9] # CAD_TEL_COM
                email = row[10]      # CAD_EMAIL
                cep = row[11]       # CAD_CEP
                endereco = row[12]  # CAD_END
                bairro = row[13]    # CAD_BAI
                cidade = row[14]    # CAD_CID
                uf = row[15]        # CAD_UF
                complemento = row[16] # CAD_COMP
                cad_sit = str(row[17]).strip() # CAD_SIT
                observacao = row[18] if row[18] else "" # CAD_OBS

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
                matricula_padrinho = int(padrinho_match.group(1)) if padrinho_match else None

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
                    }
                )

                if created:
                    count_created += 1
                else:
                    count_updated += 1

            messages.success(request, f"Importação concluída: {count_created} guardas criados, {count_updated} guardas atualizados.")
            return redirect("app:importaguardas")

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {str(e)}")
            return redirect("app:importaguardas")

    return render(request, "importaguardas.html")

@group_required('super')
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

                matricula, responsavel, paroquia, municipio, telefone, P, M, G, GG, t3G, t4G, t5G = dados

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
                    }
                )

                if not created:
                    # Atualiza os dados, caso já exista
                    apoio.responsavel = str(responsavel).strip() if responsavel else apoio.responsavel
                    apoio.paroquia = str(paroquia).strip() if paroquia else apoio.paroquia
                    apoio.municipio = str(municipio).strip() if municipio else apoio.municipio
                    apoio.telefone = str(telefone).strip() if telefone else apoio.telefone
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
                                "recebido": False,   # por padrão não recebido
                                "entregador": None,  # ainda não entregue
                                "data": timezone.now()
                            }
                        )
                linhas_processadas += 1

            messages.success(request, f"Importação concluída! {linhas_processadas} linhas processadas.")
        except Exception as e:
            messages.error(request, f"Erro ao importar arquivo: {str(e)}")
            return redirect("app:importarapoio")

        return redirect("app:importarapoio")

    return render(request, "importarapoio.html")

@group_required('super')
def deletar_camisas_por_ano(request):
    # Pega todos os anos distintos no banco, ordenados decrescente
    anos = Camisa.objects.values_list('ano', flat=True).distinct().order_by('-ano')

    if request.method == "POST":
        ano = request.POST.get('ano')
        if ano:
            try:
                ano = int(ano)
                camisas = Camisa.objects.filter(ano=ano)
                if camisas.exists():
                    # Deleta logs relacionados
                    CamisaLog.objects.filter(camisa__in=camisas).delete()
                    # Deleta camisas
                    camisas.delete()
                    messages.success(request, f"Todas as camisas e logs do ano {ano} foram deletados!")
                else:
                    messages.info(request, f"Não existem camisas cadastradas para o ano {ano}.")
            except ValueError:
                messages.error(request, "Ano inválido.")
        else:
            messages.error(request, "Informe um ano.")
        return redirect('app:deletar_camisas_por_ano')

    return render(request, 'deletar_por_ano.html', {'anos': anos})

def login_guarda(request):
    if request.user.is_authenticated:
        return redirect('app:home')
    if request.method == "POST":
        matricula = request.POST.get("matricula")
        senha = request.POST.get("senha")
        print(matricula)
        print(int(matricula))
        print(senha)

        user = authenticate(request, matricula=int(matricula), password=senha)
        print(user)
        if user is not None:
            login(request, user)
            return redirect("app:home")  # página após login
        else:
            messages.warning(request, "Matrícula ou senha incorretos.")
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
            Q(responsavel__icontains=query) |
            Q(municipio__icontains=query) |
            Q(paroquia__icontains=query)
        )

    guardas_list = []
    for g in guardas_qs:
        camisas = g.camisas.all()
        total = camisas.aggregate(total=Sum("quantidade"))["total"] or 0
        tamanhos = {c.tamanho: c.quantidade for c in camisas}

        entregue = all(c.recebido for c in camisas) if camisas else False
        entregador = camisas.first().entregador if entregue else None
        data = camisas.first().data if entregue else None

        guardas_list.append({
            "apoio": g,
            "tamanhos": tamanhos,
            "total": total,
            "entregue": entregue,
            "entregador": entregador,
            "data": data,
        })

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

    return render(request, "readapoio.html", {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "per_page": per_page,
        "per_page_options": [10, 20, 50, 100],
    })

@group_required('super','Comissão','Entregador_geral')
def entregar_apoio(request, apoio_id):
    apoio = get_object_or_404(GuardaApoio, id=apoio_id)

    if request.method == "POST":
        observacao = request.POST.get("observacao", "").strip()  # pega a observação do form

        for camisa in apoio.camisas.all():
            camisa.recebido = True
            camisa.entregador = request.user  # supondo que user -> Guarda
            camisa.data = timezone.now()
            if observacao:
                camisa.observacao = observacao  # salva a observação
            camisa.save()

        messages.success(request, f"As camisas do guarda de apoio {apoio.responsavel} foram entregues!")
        return redirect("app:readapoio")

    return redirect("app:readapoio")

@login_required
def relatorio_apoio(request):
    ano = request.GET.get("ano")

    # Definir equipes
    equipe_saude_paroquias = ['EQUIPE DE APOIO SAÚDE']  # ajustar conforme os nomes reais de paroquias de saúde

    # Filtrar guardas
    guardas = GuardaApoio.objects.all()

    tamanhos_list = ['PP','P','M','G','GG','3G','4G','5G','6G']

    # Dicionário para agregar por equipe e tamanho
    agregados = {}

    for g in guardas:
        # Identificar equipe
        if g.paroquia in equipe_saude_paroquias:
            equipe = "Equipe Saúde"
        else:
            equipe = "Guarda Apoio"

        if equipe not in agregados:
            agregados[equipe] = {t: {'entregues':0,'a_entregar':0} for t in tamanhos_list}

        camisas = g.camisas.all()
        for t in tamanhos_list:
            entregues = camisas.filter(tamanho=t, recebido=True).aggregate(qtd=Sum('quantidade'))['qtd'] or 0
            a_entregar = camisas.filter(tamanho=t, recebido=False).aggregate(qtd=Sum('quantidade'))['qtd'] or 0
            agregados[equipe][t]['entregues'] += entregues
            agregados[equipe][t]['a_entregar'] += a_entregar

    # Preparar dados para a tabela (lista de linhas)
    tabela_dados = []
    total_geral = {t: {'entregues':0,'a_entregar':0} for t in tamanhos_list}

    for equipe, tamanhos in agregados.items():
        total_equipe = {'entregues':0,'a_entregar':0}
        for t, qtds in tamanhos.items():
            tabela_dados.append({
                'equipe': equipe,
                'tamanho': t,
                'entregues': qtds['entregues'],
                'a_entregar': qtds['a_entregar'],
            })
            # acumula total por equipe
            total_equipe['entregues'] += qtds['entregues']
            total_equipe['a_entregar'] += qtds['a_entregar']
            # acumula total geral
            total_geral[t]['entregues'] += qtds['entregues']
            total_geral[t]['a_entregar'] += qtds['a_entregar']

        # adiciona linha de total por equipe
        tabela_dados.append({
            'equipe': f"Total {equipe}",
            'tamanho': '-',
            'entregues': total_equipe['entregues'],
            'a_entregar': total_equipe['a_entregar'],
        })

    # adiciona linha de total geral
    tabela_dados.append({
        'equipe': 'Total Geral',
        'tamanho': '-',
        'entregues': sum([v['entregues'] for v in total_geral.values()]),
        'a_entregar': sum([v['a_entregar'] for v in total_geral.values()]),
    })

    # Preparar dados para gráficos
    entregues_por_equipe = {e: sum([v['entregues'] for v in t.values()]) for e,t in agregados.items()}
    entregues_por_tamanho = {t: sum([v[t]['entregues'] for v in agregados.values()]) for t in tamanhos_list}
    a_entregar_por_equipe = {e: sum([v['a_entregar'] for v in t.values()]) for e,t in agregados.items()}
    a_entregar_por_tamanho = {t: sum([v[t]['a_entregar'] for v in agregados.values()]) for t in tamanhos_list}
    totais_por_equipe = {e: entregues_por_equipe[e]+a_entregar_por_equipe[e] for e in entregues_por_equipe}
    totais_por_tamanho = {t: entregues_por_tamanho[t]+a_entregar_por_tamanho[t] for t in tamanhos_list}

    # Equipe x Tamanho (linha empilhada)
    entregues_por_equipe_tamanho = {e: {t:v['entregues'] for t,v in tamanhos.items()} for e,tamanhos in agregados.items()}
    a_entregar_por_equipe_tamanho = {e: {t:v['a_entregar'] for t,v in tamanhos.items()} for e,tamanhos in agregados.items()}
    totais_por_equipe_tamanho = {e: {t:v['entregues']+v['a_entregar'] for t,v in tamanhos.items()} for e,tamanhos in agregados.items()}

    anos_qs = CamisaGuardaApoio.objects.exclude(data__isnull=True).values_list('data', flat=True)
    anos = sorted(list({d.year for d in anos_qs if d is not None}), reverse=True)
    ano_selecionado = ano

    return render(request, 'relatorios.html', {
        'tabela_dados': tabela_dados,
        'entregues_por_equipe': entregues_por_equipe,
        'entregues_por_tamanho': entregues_por_tamanho,
        'entregues_por_equipe_tamanho': entregues_por_equipe_tamanho,
        'a_entregar_por_equipe': a_entregar_por_equipe,
        'a_entregar_por_tamanho': a_entregar_por_tamanho,
        'a_entregar_por_equipe_tamanho': a_entregar_por_equipe_tamanho,
        'totais_por_equipe': totais_por_equipe,
        'totais_por_tamanho': totais_por_tamanho,
        'totais_por_equipe_tamanho': totais_por_equipe_tamanho,
        'anos': anos,
        'ano_selecionado': ano_selecionado,
    })

@login_required
def force_change_password(request):
    user = request.user

    if request.method == "POST":
        form = ForceChangePasswordForm(request.POST)
        if form.is_valid():
            senha = form.cleaned_data["new_password1"]
            user.set_password(senha)
            user.must_change_password = False
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
        'E1': '#f4b000', 'E2': '#e85c2a', 'E3': '#7ab731', 'E4': '#3fa9f5',
        'E5': '#d22f27', 'RB': '#1c3b6b', 'NB': '#f2e2b3', 'FC': '#f5f1d7',
        'PS': '#8b5c3f', 'AT': '#444444', 'NC': '#2e98a7', 'ASCOM': '#212529',
        'BS': '#212529', 'CP': '#212529', 'DR': '#212529', 'ES': '#212529',
        'SE': '#212529', 'SI': '#212529',
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
        equipes_data.append({
            "equipe": equipe,
            "total_guardas": total_guardas,
            "recebidos_guardas": recebidos_guardas,
            "nao_recebidos_guardas": total_guardas - recebidos_guardas,
            "cor": cor
        })

    # Total de camisas entregues ponderado pelo fator
    total_camisas_entregues = sum(fator_equipes(c.equipe) for c in qs.filter(recebido=True))

    # Total geral de guardas para gráfico
    total_geral_guardas = qs.count()
    recebidos_geral_guardas = qs.filter(recebido=True).count()

    total_guardas_receberam = qs.filter(recebido=True).values("guarda").distinct().count()

    context = {
        "equipes_data": json.dumps(equipes_data),
        "geral_data": json.dumps({
            "total_guardas": total_geral_guardas,
            "recebidos_guardas": recebidos_geral_guardas,
            "nao_recebidos_guardas": total_geral_guardas - recebidos_geral_guardas
        }),
        "total_guardas_receberam": total_guardas_receberam,
        "total_camisas_entregues": total_camisas_entregues,
    }

    return render(request, "monitoramento.html", context)

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
    return render(request, "minhas_entregas.html", context)

@login_required
def relatorio_camisas2(request):
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
    ordem_tamanhos = ["PP", "P", "M", "G", "GG", "3G", "4G", "5G", "6G", "XG", "UN", "ESPECIAL"]

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

        tabela_por_equipe[equipe]["tamanhos"].append({
            "tamcamisa": d["tamcamisa"],
            "entregues": entregues_fator,
            "a_entregar": pendente_fator,
        })
        tabela_por_equipe[equipe]["total_entregues"] += entregues_fator
        tabela_por_equipe[equipe]["total_pendente"] += pendente_fator

    # --- Ordena tamanhos dentro de cada equipe ---
    for equipe, info in tabela_por_equipe.items():
        info["tamanhos"].sort(
            key=lambda x: ordem_tamanhos.index(x["tamcamisa"])
            if x["tamcamisa"] in ordem_tamanhos else 99
        )

    # --- Totais gerais com fator ---
    total_geral = {
        "total_entregues": sum(e["total_entregues"] for e in tabela_por_equipe.values()),
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
    return render(request, "relatorio_camisas2.html", context)

def carregar_faiss_index():
    """
    Carrega todos os encodings do banco de dados e cria um índice FAISS na RAM.
    """
    guardas = Guarda.objects.exclude(encoding__isnull=True)
    if not guardas:
        return None, [], []

    encodings = []
    ids = []
    for g in guardas:
        try:
            enc = np.frombuffer(g.encoding, dtype=np.float64)
            encodings.append(enc)
            ids.append(g.idguarda)
        except Exception:
            continue

    encodings = np.array(encodings).astype('float32')
    index = faiss.IndexFlatL2(encodings.shape[1])  # busca por distância euclidiana
    index.add(encodings)
    return index, ids, encodings

@group_required('super','Direção')
@csrf_exempt
def reconhecimento_facial(request):
    if request.method == "GET":
        # Renderiza o HTML da câmera
        return render(request, "reconhecimento.html")

    elif request.method == "POST":
        try:
            data = request.POST.get("imagem")
            if not data:
                return JsonResponse({"status": "erro", "mensagem": "Imagem não enviada."})

            # Decodifica a imagem base64
            img_bytes = base64.b64decode(data.split(",")[1])
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (0,0), fx=0.5, fy=0.5)  # reduz ruído, aumenta performance


# Extrai encodings do rosto
            encodings = face_recognition.face_encodings(frame_resized)
            if not encodings:
                return JsonResponse({"status": "erro", "mensagem": "Nenhum rosto detectado."})

            # Busca no índice FAISS
            guarda = face_index.search(encodings[0], threshold=0.35)
            if guarda:
                return JsonResponse({
                    "status": "ok",
                    "guarda": {
                        "nome": guarda.nome,
                        "matricula": guarda.matricula,
                        "foto_url": guarda.foto.url if guarda.foto else None

                }
                })
            else:
                return JsonResponse({"status": "erro", "mensagem": "Rosto não reconhecido."})

        except Exception as e:

            return JsonResponse({"status": "erro", "mensagem": str(e)})

    else:
        return JsonResponse({"status": "erro", "mensagem": "Método inválido."}, status=405)

@group_required('super', 'Direção')
def createcamisa(request, guarda_id):
    guarda = get_object_or_404(Guarda, pk=guarda_id)
    criador = get_object_or_404(Guarda, matricula=request.user.matricula)

    if request.method == 'POST':
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
            messages.success(request, 'Camisa cadastrada com sucesso.')
            return redirect('app:readcamisa')

        else:
            # 🔴 Tratamento de erro de validação do form
            for campo, erros in form.errors.items():
                for erro in erros:
                    messages.error(
                        request,
                        f"Erro no campo '{campo}': {erro}"
                    )

    else:
        form = CamisaForm()

    return render(request, 'createcamisa.html', {
        'form': form,
        'guarda': guarda,
    })

