from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def home(request):
    return render(request, "index.html")

def mirim_home(request):
    return render(request, "index.html")


def dashboard(request):
    return render(request, "guarda/dashboard.html")


def frequencia(request):
    return render(request, "guarda/registrar_frequencia.html")


def listaGuarda(request):
    return render(request, "guarda/listaGuarda.html")


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
