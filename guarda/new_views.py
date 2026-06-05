from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from .models import Guarda


# Create your views here.
def home(request):
    return render(request, "index.html")


def mirim_home(request):
    return render(request, "index.html")


def dashboard(request):
    return render(request, "guarda/dashboard.html")


def frequencia(request):
    return render(request, "guarda/registrar_frequencia.html")


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


def cadastroEvento(request):
    return render(request, "evento/cadastroEvento.html")


def eventos(request):
    return render(request, "evento/eventos.html")


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
