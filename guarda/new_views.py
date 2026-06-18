from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date, parse_time

from evento.models import CategoriaEvento, Evento, Frequencia, Local
from .models import Guarda


META_PRESENCAS_CIRIO = 25
CATEGORIAS_PRESENCA_CIRIO = ("Missa", "Missas")


# Create your views here.
def home(request):
    return render(request, "index.html")


def mirim_home(request):
    return render(request, "index.html")


def dashboard(request):
    return render(request, "guarda/dashboard.html")


def _frequencia_context():
    filtro_categorias_cirio = Q()
    for categoria in CATEGORIAS_PRESENCA_CIRIO:
        filtro_categorias_cirio |= Q(
            frequencias__evento__categoria__nome__iexact=categoria
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


def cadastroGuarda(request):
    return render(request, "guarda/cadastroGuarda.html")


def delete_object(request):
    # TODO: Implement generic delete logic
    from django.shortcuts import redirect
    return redirect("guarda:mirim_home")
