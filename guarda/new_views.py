import json
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.utils.text import slugify

from evento.models import CategoriaEvento, Evento, Frequencia, Local
from pessoa.models import Endereco, Pessoa
from saude.models import FichaSaude
from usuario.models import Usuario
from .models import Guarda, Sacramento


META_PRESENCAS_CIRIO = 25
CATEGORIAS_PRESENCA_CIRIO = ("Missa", "Missas")
CATEGORIAS_ADORACAO = ("Adoração", "Adorações")
SENHA_TEMPORARIA_GUARDA = "Guarda2025@"
TIPOS_GUARDA_CADASTRO = {
    "aspirante": "Mirim",
    "juvenil": "Mirim",
    "efetivo": "Efetivo",
    "honorario": "Honorário",
}
CONDICOES_SAUDE_CADASTRO = (
    "autismo",
    "tdah",
    "alzheimer",
    "demencia",
    "parkinson",
    "diabetes",
    "hipertensao",
    "problema_cardiaco",
    "problema_renal",
    "osteoporose",
    "artrite",
    "usa_cadeira_rodas",
    "usa_andador",
    "usa_bengala",
    "deficiencia_visual",
    "deficiencia_auditiva",
    "usa_protese",
    "depressao",
    "ansiedade",
)


# Create your views here.
def home(request):
    return render(request, "index.html")


def mirim_home(request):
    return render(request, "index.html")


def _filtro_categoria_evento(campo, categorias):
    filtro = Q()
    for categoria in categorias:
        filtro |= Q(**{f"{campo}__iexact": categoria})
    return filtro


def _icone_categoria_dashboard(slug):
    icones = {
        "missa": "ti-building-church",
        "missas": "ti-building-church",
        "ensaio": "ti-music",
        "reuniao": "ti-users",
        "reuniao-de-formacao": "ti-users",
        "cirio": "ti-map-2",
    }
    return icones.get(slug, "ti-tag")


def _status_evento_dashboard(evento, presencas_eventos_ids, data_atual, hora_atual):
    if evento.pk in presencas_eventos_ids:
        return {
            "rotulo": "Presente",
            "classe": "pres-sim",
            "dot": "dot-blue",
        }

    is_futuro = evento.data > data_atual or (
        evento.data == data_atual and evento.hora > hora_atual
    )
    if is_futuro:
        return {
            "rotulo": "Agendado",
            "classe": "pres-fut",
            "dot": "dot-amber",
        }

    return {
        "rotulo": "Ausente",
        "classe": "pres-nao",
        "dot": "dot-gray",
    }


def _dashboard_context(guarda):
    filtro_missas = _filtro_categoria_evento(
        "evento__categoria__nome",
        CATEGORIAS_PRESENCA_CIRIO,
    )
    filtro_adoracoes = _filtro_categoria_evento(
        "evento__categoria__nome",
        CATEGORIAS_ADORACAO,
    )

    frequencias = Frequencia.objects.filter(guarda=guarda)
    total_presencas = frequencias.count()
    total_missas = frequencias.filter(filtro_missas).count()
    total_adoracoes = frequencias.filter(filtro_adoracoes).count()
    faltas_cirio = max(META_PRESENCAS_CIRIO - total_missas, 0)
    percentual_cirio = min(
        round((total_missas / META_PRESENCAS_CIRIO) * 100),
        100,
    )

    presencas_eventos_ids = set(frequencias.values_list("evento_id", flat=True))
    data_atual = timezone.localdate()
    hora_atual = timezone.localtime().time()
    eventos = Evento.objects.select_related("categoria", "local").order_by(
        "-data", "-hora"
    )[:20]

    eventos_dashboard = []
    categorias_por_slug = {}
    for evento in eventos:
        categoria_nome = evento.categoria.nome
        categoria_slug = slugify(categoria_nome) or "outro"
        status = _status_evento_dashboard(
            evento,
            presencas_eventos_ids,
            data_atual,
            hora_atual,
        )
        eventos_dashboard.append(
            {
                "categoria": categoria_nome,
                "categoria_slug": categoria_slug,
                "nome": categoria_nome,
                "local": evento.local.nome,
                "data": evento.data,
                "hora": evento.hora,
                "busca": f"{categoria_nome} {evento.local.nome}".lower(),
                "status": status,
            }
        )
        categorias_por_slug.setdefault(
            categoria_slug,
            {
                "slug": categoria_slug,
                "nome": categoria_nome,
                "icone": _icone_categoria_dashboard(categoria_slug),
            },
        )

    return {
        "guarda": guarda,
        "ano_cirio": data_atual.year,
        "meta_presencas_cirio": META_PRESENCAS_CIRIO,
        "total_presencas": total_presencas,
        "total_missas": total_missas,
        "total_adoracoes": total_adoracoes,
        "faltas_cirio": faltas_cirio,
        "percentual_cirio": percentual_cirio,
        "eventos_dashboard": eventos_dashboard,
        "categorias_eventos": categorias_por_slug.values(),
        "guarda_qr_data": {
            "nome": guarda.nome,
            "matricula": guarda.matricula,
            "tipo": guarda.tipo or "Guarda",
            "status": "Ativo" if guarda.is_ativo else "Inativo",
        },
    }


@login_required
def dashboard(request):
    try:
        guarda = request.user.pessoa.guarda
    except ObjectDoesNotExist:
        messages.error(request, "Usuário sem guarda vinculado.")
        return redirect("app:home")

    return render(request, "guarda/dashboard.html", _dashboard_context(guarda))


def _frequencia_context():
    filtro_categorias_cirio = _filtro_categoria_evento(
        "frequencias__evento__categoria__nome",
        CATEGORIAS_PRESENCA_CIRIO,
    )

    mirins = list(
        Guarda.objects.select_related("pessoa")
        .filter(tipo__iexact="Mirim", is_ativo=True)
        .annotate(
            total_presencas_cirio=Count(
                "frequencias",
                filter=filtro_categorias_cirio,
                distinct=True,
            )
        )
        .order_by("pessoa__nome")
    )
    for mirim in mirins:
        mirim.faltas_para_cirio = max(
            META_PRESENCAS_CIRIO - mirim.total_presencas_cirio,
            0,
        )

    eventos = Evento.objects.select_related("categoria", "local").order_by(
        "-data", "-hora"
    )
    return {
        "mirins": mirins,
        "eventos": eventos,
        "meta_presencas_cirio": META_PRESENCAS_CIRIO,
    }


def frequencia(request):
    if request.method == "POST":
        guarda_pk = request.POST.get("mirim")
        evento_pk = request.POST.get("evento")

        if not guarda_pk or not evento_pk:
            messages.error(request, "Selecione um mirim e um evento.")
            return redirect("guarda:frequencia")

        try:
            guarda = Guarda.objects.get(
                pk=guarda_pk, tipo__iexact="Mirim", is_ativo=True
            )
            evento = Evento.objects.get(pk=evento_pk)
        except (Guarda.DoesNotExist, Evento.DoesNotExist, ValueError):
            messages.error(request, "Mirim ou evento inválido.")
            return redirect("guarda:frequencia")

        _, criado = Frequencia.objects.get_or_create(
            guarda=guarda,
            evento=evento,
            defaults={"reconhecimento_facial": False},
        )

        if criado:
            messages.success(request, "Presença registrada com sucesso.")
        else:
            messages.info(request, "Essa presença já estava registrada.")

        return redirect("guarda:frequencia")

    return render(
        request,
        "guarda/registrar_frequencia.html",
        _frequencia_context(),
    )


def _status_guarda(guarda):
    return "ativo" if guarda.is_ativo else "inativo"


def _serialize_guarda(guarda):
    return {
        "id": guarda.pk,
        "nome": guarda.nome,
        "matricula": guarda.matricula,
        "ministerio": guarda.ministerio or guarda.paroquia or "",
        "status": _status_guarda(guarda),
        "tipo": guarda.tipo or "",
    }


def _guardas_queryset(request):
    search = request.GET.get("search", "").strip()
    tipo = request.GET.get("tipo", "Mirim").strip()

    guardas = Guarda.objects.select_related("pessoa").order_by("pessoa__nome")

    if tipo and tipo.lower() != "todos":
        guardas = guardas.filter(tipo__iexact=tipo)

    if search:
        guardas = guardas.filter(
            Q(pessoa__nome__icontains=search) | Q(matricula__icontains=search)
        )

    return guardas


def listaGuarda(request):
    guardas_data = [_serialize_guarda(guarda) for guarda in _guardas_queryset(request)]
    return render(
        request,
        "guarda/listaGuarda.html",
        {
            "guardas_data": guardas_data,
            "guardas_total": len(guardas_data),
        },
    )


def listaGuardaData(request):
    guardas_data = [_serialize_guarda(guarda) for guarda in _guardas_queryset(request)]
    return JsonResponse({"guardas": guardas_data, "total": len(guardas_data)})


def _cadastro_evento_context():
    categorias = CategoriaEvento.objects.filter(is_ativo=True).order_by("nome")
    locais = Local.objects.filter(is_ativo=True).order_by("nome")
    return {
        "categorias": categorias,
        "locais": locais,
        "categorias_por_id": {
            categoria.pk: categoria.nome for categoria in categorias
        },
        "locais_por_id": {local.pk: local.nome for local in locais},
    }


def _cadastro_evento_error(mensagem, status=400):
    return JsonResponse({"ok": False, "error": mensagem}, status=status)


def cadastroEvento(request):
    if request.method == "POST":
        categoria_pk = request.POST.get("categoria_id")
        local_pk = request.POST.get("local_id")
        data_evento = parse_date(request.POST.get("data", ""))
        hora_evento = parse_time(request.POST.get("hora", ""))

        if not categoria_pk or not local_pk or not data_evento or not hora_evento:
            return _cadastro_evento_error("Preencha os campos obrigatórios.")

        try:
            categoria = CategoriaEvento.objects.get(pk=categoria_pk, is_ativo=True)
            local = Local.objects.get(pk=local_pk, is_ativo=True)
        except (CategoriaEvento.DoesNotExist, Local.DoesNotExist, ValueError):
            return _cadastro_evento_error("Categoria ou local inválido.")

        try:
            Evento.objects.create(
                categoria=categoria,
                local=local,
                data=data_evento,
                hora=hora_evento,
            )
        except IntegrityError:
            return _cadastro_evento_error(
                "Já existe um evento com essa categoria, local, data e hora.",
                status=409,
            )

        return JsonResponse(
            {
                "ok": True,
                "message": "Evento cadastrado com sucesso.",
                "redirect_url": reverse("guarda:eventos"),
            }
        )

    return render(
        request,
        "evento/cadastroEvento.html",
        _cadastro_evento_context(),
    )


def eventos(request):
    eventos = (
        Evento.objects.select_related("categoria", "local")
        .annotate(total_presencas=Count("frequencias"))
        .order_by("-data", "-hora")
    )
    return render(request, "evento/eventos.html", {"eventos": eventos})


def relatorio(request):
    return render(request, "evento/relatorio.html")


def admin(request):
    return render(request, "evento/admin.html")


def _cadastro_guarda_error(mensagem, status=400):
    return JsonResponse({"ok": False, "error": mensagem}, status=status)


def _clean_optional(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def _clean_required(valor):
    return _clean_optional(valor) or ""


def _parse_optional_date(valor, campo):
    valor = _clean_optional(valor)
    if not valor:
        return None
    parsed = parse_date(valor)
    if parsed is None:
        raise ValueError(f"{campo} inválida.")
    return parsed


def _dict_payload(valor):
    return valor if isinstance(valor, dict) else {}


def _tem_algum_valor(dados):
    return any(_clean_optional(valor) for valor in dados.values())


def _map_tipo_guarda(tipo):
    tipo = _clean_required(tipo).lower()
    return TIPOS_GUARDA_CADASTRO.get(tipo)


def _normalizar_matricula(matricula):
    matricula = _clean_optional(matricula)
    if not matricula:
        return None
    matricula = "".join(caractere for caractere in matricula if caractere.isdigit())
    if len(matricula) != 4:
        raise ValueError("A matrícula deve ter exatamente 4 dígitos.")
    return matricula


def _gerar_matricula_disponivel():
    usadas = set(Guarda.objects.values_list("matricula", flat=True))
    usadas.update(Usuario.objects.values_list("usuario", flat=True))
    disponiveis = [
        f"{numero:04d}"
        for numero in range(1, 10000)
        if f"{numero:04d}" not in usadas
    ]
    if not disponiveis:
        return None
    return random.choice(disponiveis)


def _resolver_matricula(raw_matricula):
    matricula = _normalizar_matricula(raw_matricula)
    if matricula:
        if (
            Guarda.objects.filter(matricula=matricula).exists()
            or Usuario.objects.filter(usuario=matricula).exists()
        ):
            raise ValueError("Matrícula já cadastrada.")
        return matricula
    return _gerar_matricula_disponivel()


def _validar_duplicidades_pessoa(cpf, email, rg):
    if Pessoa.objects.filter(cpf=cpf).exists():
        return "CPF já cadastrado."
    if Pessoa.objects.filter(email__iexact=email).exists():
        return "E-mail já cadastrado."
    if rg and Pessoa.objects.filter(rg=rg).exists():
        return "RG já cadastrado."
    return None


def cadastroGuarda(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return _cadastro_guarda_error("Envie dados em JSON válido.")

        if not isinstance(payload, dict):
            return _cadastro_guarda_error("Payload inválido.")

        endereco_payload = _dict_payload(payload.get("endereco"))
        ficha_payload = _dict_payload(payload.get("ficha_saude"))
        guarda_payload = _dict_payload(payload.get("guarda"))
        sacramento_payload = _dict_payload(payload.get("sacramento"))

        nome = _clean_required(payload.get("nome"))
        cpf = _clean_required(payload.get("cpf"))
        email = _clean_required(payload.get("email")).lower()
        rg = _clean_optional(payload.get("rg"))
        ministerio = _clean_required(guarda_payload.get("ministerio"))
        tipo = _map_tipo_guarda(guarda_payload.get("tipo"))

        try:
            turma = int(guarda_payload.get("turma"))
        except (TypeError, ValueError):
            turma = None

        if not nome:
            return _cadastro_guarda_error("Informe o nome.")
        if not cpf:
            return _cadastro_guarda_error("Informe o CPF.")
        if not email:
            return _cadastro_guarda_error("Informe o e-mail.")
        if not turma or turma <= 0:
            return _cadastro_guarda_error("Informe a turma.")
        if tipo is None:
            return _cadastro_guarda_error("Tipo de guarda inválido.")
        if not ministerio:
            return _cadastro_guarda_error("Informe o ministério.")

        erro_duplicidade = _validar_duplicidades_pessoa(cpf, email, rg)
        if erro_duplicidade:
            return _cadastro_guarda_error(erro_duplicidade, status=409)

        try:
            matricula = _resolver_matricula(guarda_payload.get("matricula"))
            data_nascimento = _parse_optional_date(
                payload.get("data_nascimento"),
                "Data de nascimento",
            )
            data_ingresso = _parse_optional_date(
                guarda_payload.get("data_ingresso"),
                "Data de ingresso",
            )
            data_batismo = _parse_optional_date(
                sacramento_payload.get("data_batismo"),
                "Data de batismo",
            )
            data_primeira_eucaristia = _parse_optional_date(
                sacramento_payload.get("data_primeira_eucaristia"),
                "Data da primeira eucaristia",
            )
            data_crisma = _parse_optional_date(
                sacramento_payload.get("data_crisma"),
                "Data de crisma",
            )
        except ValueError as exc:
            status = 409 if "já cadastrada" in str(exc) else 400
            return _cadastro_guarda_error(str(exc), status=status)

        if matricula is None:
            return _cadastro_guarda_error(
                "Não há matrículas disponíveis.",
                status=409,
            )

        try:
            with transaction.atomic():
                pessoa = Pessoa.objects.create(
                    nome=nome,
                    cpf=cpf,
                    rg=rg,
                    email=email,
                    telefone=_clean_optional(payload.get("telefone")),
                    data_nascimento=data_nascimento,
                    genero=_clean_optional(payload.get("genero")),
                    estado_civil=_clean_optional(payload.get("estado_civil")),
                )

                if _tem_algum_valor(endereco_payload):
                    Endereco.objects.create(
                        pessoa=pessoa,
                        cep=_clean_optional(endereco_payload.get("cep")),
                        uf=_clean_optional(endereco_payload.get("uf")),
                        logradouro=_clean_optional(endereco_payload.get("logradouro")),
                        numero=_clean_optional(endereco_payload.get("numero")),
                        complemento=_clean_optional(endereco_payload.get("complemento")),
                        bairro=_clean_optional(endereco_payload.get("bairro")),
                        cidade=_clean_optional(endereco_payload.get("cidade")),
                    )

                ficha_dados = {
                    campo: bool(ficha_payload.get(campo))
                    for campo in CONDICOES_SAUDE_CADASTRO
                }
                ficha_dados.update(
                    {
                        "tipo_sanguineo": _clean_optional(
                            ficha_payload.get("tipo_sanguineo")
                        ),
                        "alergia": _clean_optional(ficha_payload.get("alergia")),
                        "intolerancia_alimentar": _clean_optional(
                            ficha_payload.get("intolerancia_alimentar")
                        ),
                        "uso_medicamento_controlado": _clean_optional(
                            ficha_payload.get("uso_medicamento_controlado")
                        ),
                        "plano_saude": _clean_optional(ficha_payload.get("plano_saude")),
                        "contato_emergencia_nome": _clean_optional(
                            ficha_payload.get("contato_emergencia_nome")
                        ),
                        "contato_emergencia_telefone": _clean_optional(
                            ficha_payload.get("contato_emergencia_telefone")
                        ),
                        "observacao": _clean_optional(ficha_payload.get("observacao")),
                    }
                )
                FichaSaude.objects.create(pessoa=pessoa, **ficha_dados)

                guarda = Guarda.objects.create(
                    pessoa=pessoa,
                    matricula=matricula,
                    turma=turma,
                    tipo=tipo,
                    ministerio=ministerio,
                    paroquia=_clean_optional(guarda_payload.get("paroquia")),
                    tamanho_camisa=_clean_optional(
                        guarda_payload.get("tamanho_camisa")
                    ),
                    data_ingresso=data_ingresso,
                    observacao=_clean_optional(guarda_payload.get("observacao")),
                )

                Usuario.objects.create_user(
                    usuario=guarda.matricula,
                    password=SENHA_TEMPORARIA_GUARDA,
                    pessoa=pessoa,
                    trocar_senha=True,
                    is_ativo=True,
                    is_funcionario=False,
                )

                Sacramento.objects.create(
                    guarda=guarda,
                    batismo=bool(sacramento_payload.get("batismo")),
                    primeira_eucaristia=bool(
                        sacramento_payload.get("primeira_eucaristia")
                    ),
                    crisma=bool(sacramento_payload.get("crisma")),
                    ordem=bool(sacramento_payload.get("ordem")),
                    data_batismo=data_batismo,
                    data_primeira_eucaristia=data_primeira_eucaristia,
                    data_crisma=data_crisma,
                )
        except IntegrityError:
            return _cadastro_guarda_error(
                "Já existe cadastro com CPF, e-mail, RG ou matrícula informados.",
                status=409,
            )

        return JsonResponse(
            {
                "ok": True,
                "guarda_id": guarda.pk,
                "matricula": guarda.matricula,
                "redirect_url": reverse("guarda:guardas"),
            }
        )

    return render(request, "guarda/cadastroGuarda.html")


def delete_object(request):
    # TODO: Implement generic delete logic
    from django.shortcuts import redirect
    return redirect("guarda:mirim_home")
