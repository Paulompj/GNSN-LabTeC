from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

# from app.decorators import group_required

from .forms import CategoriaEventoForm, LocalForm
from .models import CategoriaEvento, Local


# @group_required("super")
def categoria_list(request):
    categorias = CategoriaEvento.objects.all().order_by("nome")
    return render(
        request,
        "evento/categorias_list.html",
        {"categorias": categorias},
    )


# @group_required("super")
def categoria_create(request):
    form = CategoriaEventoForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Categoria cadastrada com sucesso.")
        return redirect("evento:categoria_list")

    return render(request, "evento/categorias_form.html", {"form": form})


# @group_required("super")
def categoria_update(request, pk):
    categoria = get_object_or_404(CategoriaEvento, pk=pk)
    form = CategoriaEventoForm(request.POST or None, instance=categoria)

    if form.is_valid():
        form.save()
        messages.success(request, "Categoria atualizada com sucesso.")
        return redirect("evento:categoria_list")

    return render(request, "evento/categorias_form.html", {"form": form})


# @group_required("super")
@require_POST
def categoria_delete(request, pk):
    categoria = get_object_or_404(CategoriaEvento, pk=pk)

    try:
        categoria.delete()
        messages.success(request, "Categoria excluída com sucesso.")
    except ProtectedError:
        messages.error(
            request,
            "Categoria não excluída porque está vinculada a um evento.",
        )

    return redirect("evento:categoria_list")


# @group_required("super")
def local_list(request):
    locais = Local.objects.all().order_by("nome")
    return render(
        request,
        "evento/locais_list.html",
        {"locais": locais},
    )


# @group_required("super")
def local_create(request):
    form = LocalForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Local cadastrado com sucesso.")
        return redirect("evento:local_list")

    return render(request, "evento/locais_form.html", {"form": form})


# @group_required("super")
def local_update(request, pk):
    local_evento = get_object_or_404(Local, pk=pk)
    form = LocalForm(request.POST or None, instance=local_evento)

    if form.is_valid():
        form.save()
        messages.success(request, "Local atualizado com sucesso.")
        return redirect("evento:local_list")

    return render(request, "evento/locais_form.html", {"form": form})


# @group_required("super")
@require_POST
def local_delete(request, pk):
    local_evento = get_object_or_404(Local, pk=pk)

    try:
        local_evento.delete()
        messages.success(request, "Local excluído com sucesso.")
    except ProtectedError:
        messages.error(
            request,
            "Local não excluído porque está vinculado a um evento.",
        )

    return redirect("evento:local_list")
