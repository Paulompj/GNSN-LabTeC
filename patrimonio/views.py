from .models import Setor, Categoria, Material, Estoque, Emprestimo
from .forms import SetorForm, CategoriaForm, MaterialForm, EstoqueForm, EmprestimoForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required

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
            return redirect("patrimonio:home")
        return _wrapped_view
    return decorator

@group_required('super','Patrimonio_adm')
def setor_list(request):
    setores = Setor.objects.all()
    return render(request, "patrimonio/setor_list.html", {"setores": setores})

@group_required('super','Patrimonio_adm')
def setor_form(request, id=None):
    setor = get_object_or_404(Setor, pk=id) if id else None

    if request.method == "POST":
        form = SetorForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            messages.success(request, "Setor salvo com sucesso!")
            return redirect("patrimonio:setor_list")
    else:
        form = SetorForm(instance=setor)

    return render(request, "patrimonio/setor_form.html", {"form": form, "setor": setor})

@group_required('super','Patrimonio_adm')
def setor_delete(request, id):
    setor = get_object_or_404(Setor, pk=id)

    if request.method == "POST":
        setor.delete()
        messages.success(request, "Setor deletado com sucesso!")
    return redirect("patrimonio:setor_list")

# LISTAGEM
@group_required('super','Patrimonio_adm')
def categoria_list(request):
    categorias = Categoria.objects.all()
    return render(request, "patrimonio/categoria_list.html", {"categorias": categorias})

# CREATE + EDIT (mesma tela)
@group_required('super','Patrimonio_adm')
def categoria_form(request, id=None):
    categoria = get_object_or_404(Categoria, pk=id) if id else None

    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria salvo com sucesso!")
            return redirect("patrimonio:categoria_list")
    else:
        form = CategoriaForm(instance=categoria)

    return render(
        request,
        "patrimonio/categoria_form.html",
        {"form": form, "categoria": categoria},
    )

# DELETE via POST (modal)
@group_required('super','Patrimonio_adm')
def categoria_delete(request, id):
    categoria = get_object_or_404(Categoria, pk=id)

    if request.method == "POST":
        categoria.delete()
        messages.success(request, "Categoria deletado com sucesso!")

    return redirect("patrimonio:categoria_list")

@group_required('super','Patrimonio_adm')
def material_list(request):
    materiais = (
        Material.objects
        .select_related("categoria", "setor")
        .order_by("categoria__nome", "nome")
    )

    categorias = Categoria.objects.order_by("nome")

    return render(
        request,
        "patrimonio/material_list.html",
        {
            "materiais": materiais,
            "categorias": categorias,
        },
    )

# CREATE + EDIT (mesma tela)
@group_required('super','Patrimonio_adm')
def material_form(request, id=None):
    material = get_object_or_404(Material, pk=id) if id else None

    if request.method == "POST":
        form = MaterialForm(request.POST, instance=material)

        if form.is_valid():
            material = form.save(commit=False)

            # Regra de negócio futura pode entrar aqui
            # Ex: gerar número de patrimônio automático

            material.save()
            messages.success(request, "Material salvo com sucesso!")
            return redirect("patrimonio:material_list")
    else:
        form = MaterialForm(instance=material)

    return render(
        request,
        "patrimonio/material_form.html",
        {"form": form, "material": material},
    )

# DELETE via POST (modal)
@group_required('super','Patrimonio_adm')
def material_delete(request, id):
    material = get_object_or_404(Material, pk=id)

    if request.method == "POST":
        material.delete()
        messages.success(request, "Material deletado com sucesso!")

    return redirect("patrimonio:material_list")

# LISTAGEM
@group_required('super','Patrimonio_adm')
def estoque_list(request):
    estoques = (
        Estoque.objects
        .select_related("material", "material__categoria", "material__setor")
        .order_by("material__nome")
    )

    return render(
        request,
        "patrimonio/estoque_list.html",
        {"estoques": estoques},
    )

# CREATE + EDIT (mesma tela)
@group_required('super','Patrimonio_adm')
def estoque_form(request, id=None):
    estoque = get_object_or_404(Estoque, pk=id) if id else None
    qtd = 0
    qtd_estoque = 0

    if request.method == "POST":
        form = EstoqueForm(request.POST, instance=estoque)

        if form.is_valid():
            estoque = form.save(commit=False)

            if estoque.id:
                qtd = get_object_or_404(Material, pk=estoque.material.id).qtd_disponivel
                qtd_estoque = get_object_or_404(Estoque, pk=estoque.id).quantidade
                print(qtd)
            else:
                qtd = 0

            # impedir duplicidade de estoque para o mesmo material
            if Estoque.objects.filter(material=estoque.material).exists():
                tmp = qtd + estoque.quantidade - qtd_estoque
                estoque.material.qtd_disponivel = tmp
                estoque.material.save()
                estoque.save()
                messages.success(request, "Este material já possui controle de estoque. Estoque salvo com sucesso e quantidades atualizadas!")
                return redirect("patrimonio:estoque_list")
            else:
                tmp = qtd + estoque.quantidade - qtd_estoque
                estoque.material.qtd_disponivel = tmp
                estoque.material.save()
                estoque.save()
                messages.success(request, "Estoque salvo com sucesso!")
                return redirect("patrimonio:estoque_list")
    else:
        form = EstoqueForm(instance=estoque)

    return render(
        request,
        "patrimonio/estoque_form.html",
        {"form": form, "estoque": estoque},
    )

# DELETE via POST (modal)
@group_required('super','Patrimonio_adm')
def estoque_delete(request, id):
    estoque = get_object_or_404(Estoque, pk=id)

    if request.method == "POST":
        estoque.material.qtd_disponivel -= estoque.quantidade
        estoque.material.save()
        estoque.delete()
        messages.success(request, "Estoque deletado com sucesso!")

    return redirect("patrimonio:estoque_list")

@group_required('super','Patrimonio_adm','Patrimonio_solicitante')
def emprestimo_list(request):
    is_patrimonio_adm = request.user.groups.filter(name="Patrimonio_adm").exists()
    emprestimos = (
        Emprestimo.objects
        .select_related("material", "solicitante", "retirante")
        .order_by("-data_solicitacao")
    )

    if not is_patrimonio_adm:
        emprestimos = emprestimos.filter(solicitante=request.user)

    return render(request, "patrimonio/emprestimo_list.html", {
        "emprestimos": emprestimos,
        "is_patrimonio_adm":is_patrimonio_adm
    })

@group_required('super','Patrimonio_adm','Patrimonio_solicitante')
def emprestimo_form(request, pk=None):
    instance = get_object_or_404(Emprestimo, pk=pk) if pk else None
    is_adm = request.user.groups.filter(name="Patrimonio_adm").exists()

    if request.method == "POST":
        form = EmprestimoForm(request.POST, instance=instance)

        if form.is_valid():

            emprestimo = form.save(commit=False)

            #solicitante obrigatório = guarda logado (se não for adm)
            if not is_adm:
                emprestimo.solicitante = request.user

            #validação de estoque apenas na criação
            if not instance:
                material = get_object_or_404(Material, pk=emprestimo.material.id)

                if material.qtd_disponivel-emprestimo.quantidade < 0:
                    messages.error(request, "Material sem estoque disponível.")
                    return render(request, "patrimonio/emprestimo_form.html", {"form": form})

            emprestimo.save()
            messages.success(request, "Solicitação registrada com sucesso.")
            return redirect("patrimonio:emprestimo_list")

    else:
        form = EmprestimoForm(instance=instance)

        # esconder solicitante se não for ADM
        if not is_adm:
            form.fields["solicitante"].initial = request.user
            form.fields["solicitante"].disabled = True
            form.fields["retirante"].required = False

    return render(request, "patrimonio/emprestimo_form.html", {"form": form})

@group_required('super','Patrimonio_adm','Patrimonio_solicitante')
def emprestimo_delete(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    material = get_object_or_404(Material, pk=emprestimo.material.id)

    if request.method == "POST":
        if emprestimo.status in ["aprovado", "retirado", "atrasado"]:
            material.qtd_disponivel += emprestimo.quantidade
        emprestimo.status = "cancelado"
        emprestimo.save()
        material.save()
        messages.success(request, "Empréstimo excluído.")
        return redirect("patrimonio:emprestimo_list")
@group_required('super','Patrimonio_adm')
def emprestimo_aprovar(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    material = get_object_or_404(Material, pk=emprestimo.material.id)

    if material.qtd_disponivel-emprestimo.quantidade < 0:
        messages.error(request, "Material sem estoque disponível.")
        return redirect("patrimonio:emprestimo_list")


    # somente patrimônio pode aprovar
    if not request.user.groups.filter(name="Patrimonio_adm").exists():
        messages.error(request, "Você não tem permissão para aprovar.")
        return redirect("patrimonio:emprestimo_list")

    if emprestimo.status != "solicitado":
        messages.warning(request, "Somente solicitações pendentes podem ser aprovadas.")
        return redirect("patrimonio:emprestimo_list")

    material.qtd_disponivel -= emprestimo.quantidade
    emprestimo.status = "aprovado"
    emprestimo.responsavel_patrimonio = request.user
    emprestimo.data_retirada = timezone.now()
    emprestimo.save()
    material.save()


    messages.success(request, "Solicitação aprovada com sucesso.")
    return redirect("patrimonio:emprestimo_list")

@group_required('super','Patrimonio_adm')
def emprestimo_devolver(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    material = get_object_or_404(Material, pk=emprestimo.material.id)

    if emprestimo.status not in ["retirado", "aprovado"]:
        messages.warning(request, "Somente itens retirados podem ser devolvidos.")
        return redirect("patrimonio:emprestimo_list")

    material.qtd_disponivel += emprestimo.quantidade
    emprestimo.status = "devolvido"
    emprestimo.data_devolucao = timezone.now()
    emprestimo.save()
    material.save()

    messages.success(request, "Devolução registrada com sucesso.")
    return redirect("patrimonio:emprestimo_list")

@group_required('super','Patrimonio_adm','Patrimonio_solicitante')
def emprestimo_retirar(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)

    # só pode retirar se aprovado
    if emprestimo.status != "aprovado":
        messages.warning(request, "Somente solicitações aprovadas podem ser retiradas.")
        return redirect("patrimonio:emprestimo_list")

    if request.method == "POST":
        # atualizar status
        emprestimo.status = "retirado"
        emprestimo.retirante = request.user
        emprestimo.data_retirada = timezone.now()
        emprestimo.save()

        messages.success(request, "Empréstimo retirado com sucesso.")
        return redirect("patrimonio:emprestimo_termo", pk=emprestimo.pk)

    return redirect("patrimonio:emprestimo_list")

@group_required('super','Patrimonio_adm','Patrimonio_solicitante')
def emprestimo_termo(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)

    # só pode gerar termo se o status for "retirado"
    if emprestimo.status != "retirado":
        messages.warning(request, "Somente itens retirados podem ter termo de posse.")
        return redirect("patrimonio:emprestimo_list")

    return render(request, "patrimonio/emprestimo_termo.html", {
        "emprestimo": emprestimo,
        "entregador": request.user
    })

@login_required
def relatorio_validade(request):
    hoje = timezone.now().date()
    limite = hoje + timedelta(days=30)

    estoques = (
        Estoque.objects
        .select_related("material", "material__categoria", "material__setor")
        .filter(validade__isnull=False)
        .order_by("validade")
    )

    context = {
        "estoques": estoques,
        "hoje": hoje,
        "limite": limite,
    }

    return render(request, "patrimonio/validade.html", context)

@login_required
def relatorio_emprestimos_antigos(request):
    emprestimos = (
        Emprestimo.objects
        .select_related("material", "solicitante", "retirante")
        .filter(status__in=["aprovado", "retirado", "atrasado"])
        .order_by("data_retirada", "data_solicitacao")
    )

    hoje = timezone.now()

    return render(request, "patrimonio/emprestimos_antigos.html", {
        "emprestimos": emprestimos,
        "hoje": hoje,
    })

@login_required
def relatorio_estoque(request):
    hoje = timezone.now().date()
    limite_alerta = hoje + timedelta(days=30)

    estoques = (
        Estoque.objects
        .select_related("material")
        .order_by("validade", "material__nome")
    )

    return render(
        request,
        "patrimonio/estoque.html",
        {
            "estoques": estoques,
            "hoje": hoje,
            "limite_alerta": limite_alerta,
        },
    )