from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def home(request):
    return HttpResponse("home")


def dashboard(request):
    return render(request, "mirim/dashboard.html")


def frequencia(request):
    return render(request, "mirim/frequencia.html")


def listaGuarda(request):
    return render(request, "mirim/listaGuarda.html")


def cadastroEvento(request):
    return render(request, "mirim/cadastroEvento.html")


def eventos(request):
    return render(request, "mirim/eventos.html")


def relatorio(request):
    return render(request, "mirim/relatorio.html")


def admin(request):
    return render(request, "mirim/admin.html")


def cadastroGuarda(request):
    return render(request, "mirim/cadastroGuarda.html")
