from django.http import JsonResponse

from .forms import CategoriaEventoForm, LocalForm, GuardaMirimForm, EventoForm, FrequenciaForm, CheckinMatriculaForm, CirioForm, RegraCirioFormSet, inlineformset_factory
from .models import CategoriaEvento, Local, GuardaMirim, Evento, Frequencia, Cirio, RegraCirio
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.conf import settings
from datetime import date
import math
# Create your views here.

def group_required(*group_names):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect("mirim:home")
        return _wrapped_view
    return decorator

@login_required
def home(request):
    return render(request, 'index.html')

def enviar_email_participacao(guarda, evento):
    if not guarda.email:
        return

    send_mail(
        subject="Participação registrada",
        message=f"Sua presença no evento {evento} foi registrada com sucesso.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[guarda.email],
        fail_silently=True,
    )

def enviar_email_baixa_frequencia(guarda):
    if not guarda.email:
        return

    send_mail(
        subject="Alerta de baixa frequência",
        message="Sua frequência está abaixo do esperado. Procure participar das missas semanais.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[guarda.email],
        fail_silently=True,
    )

@login_required
def dashboard(request):

    ano = request.GET.get("ano")

    if ano:
        cirio = get_object_or_404(Cirio, ano=ano)
    else:
        cirio = Cirio.objects.filter(ativo=True).first()

    cirios = Cirio.objects.all().order_by("ano")
    guardas = GuardaMirim.objects.all()

    hoje = date.today()

    status_count = {
        "apto": 0,
        "tendencia": 0,
        "baixo": 0,
        "critico": 0,
        "inapto": 0,
    }

    total_guardas = guardas.count()

    total_dias = (cirio.termino - cirio.inicio).days
    dias_passados = (min(hoje, cirio.termino) - cirio.inicio).days

    semanas_totais = total_dias / 7 if total_dias > 0 else 1
    semanas_passadas = max(dias_passados / 7, 0)

    for guarda in guardas:

        frequencias = guarda.frequencias.filter(
            evento__data__range=(cirio.inicio, cirio.termino)
        )

        status_categoria = []
        progresso = []

        for regra in cirio.regras.select_related("categoria"):

            total = frequencias.filter(
                evento__categoria=regra.categoria
            ).count()

            necessario = regra.quantidade_necessaria

            esperado = math.ceil((semanas_passadas / semanas_totais) * necessario)

            progresso.append((total, necessario))

            if total >= necessario:
                status_categoria.append("apto")

            elif total >= esperado:
                status_categoria.append("tendencia")

            elif total < (esperado * 0.5):
                status_categoria.append("critico")

            else:
                status_categoria.append("baixo")

        # ===== STATUS FINAL =====
        if all(t >= n for t, n in progresso if n > 0):
            status = "apto"

        elif hoje > cirio.termino:
            status = "inapto"

        elif any(s == "critico" for s in status_categoria):
            status = "critico"

        elif all(s in ["apto", "tendencia"] for s in status_categoria):
            status = "tendencia"

        else:
            status = "baixo"

        status_count[status] += 1

    categorias_chart = (
        Frequencia.objects
        .filter(evento__data__range=(cirio.inicio, cirio.termino))
        .values("evento__categoria__nome")
        .annotate(total=Count("id"))
    )

    return render(request, "mirim/dashboard.html", {
        "cirio": cirio,
        "cirios": cirios,
        "total_guardas": total_guardas,
        "status_count": status_count,
        "categorias_chart": categorias_chart,
    })

@group_required('super','Mirim_adm')
def categoria_list(request):
    categorias = CategoriaEvento.objects.all()
    return render(request, "mirim/categorias_list.html", {"categorias": categorias})

@group_required('super','Mirim_adm')
def categoria_create(request):
    form = CategoriaEventoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Categoria cadastrada com sucesso.")
        return redirect("mirim:categoria_list")

    return render(request, "mirim/categorias_form.html", {"form": form})

@group_required('super','Mirim_adm')
def local_list(request):
    locais = Local.objects.all()
    return render(request, "mirim/locais_list.html", {"locais": locais})

@group_required('super','Mirim_adm')
def local_create(request):
    form = LocalForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Local cadastrado com sucesso.")
        return redirect("mirim:local_list")

    return render(request, "mirim/locais_form.html", {"form": form})

@group_required('super','Mirim_adm')
def guarda_list(request):
    guardas = GuardaMirim.objects.all()
    return render(request, "mirim/mirim_list.html", {"guardas": guardas})

@group_required('super','Mirim_adm')
def guarda_create(request):
    form = GuardaMirimForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Guarda cadastrado com sucesso.")
        return redirect("mirim:guarda_list")

    return render(request, "mirim/mirim_form.html", {"form": form})

@group_required('super','Mirim_adm')
def evento_list(request):
    eventos = Evento.objects.select_related("categoria", "local")
    return render(request, "mirim/eventos_list.html", {"eventos": eventos})

@group_required('super','Mirim_adm')
def evento_create(request):
    form = EventoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Evento criado com sucesso.")
        return redirect("mirim:evento_list")

    return render(request, "mirim/eventos_form.html", {"form": form})

@group_required('super','Mirim_adm')
def evento_list(request):
    eventos = Evento.objects.select_related("categoria", "local")
    return render(request, "mirim/eventos_list.html", {"eventos": eventos})

@group_required('super','Mirim_adm')
def evento_create(request):
    form = EventoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Evento criado com sucesso.")
        return redirect("mirim:evento_list")

    return render(request, "mirim/eventos_form.html", {"form": form})

@group_required('super','Mirim_adm')
def frequencia_create(request):
    form = FrequenciaForm(request.POST or None)

    if form.is_valid():
        frequencia = form.save()

        enviar_email_participacao(frequencia.guarda, frequencia.evento)

        hoje = date.today()
        inicio = date(hoje.year, 9, 1)
        if hoje < inicio:
            inicio = date(hoje.year - 1, 9, 1)
        semanas = (hoje - inicio).days // 7

        if frequencia.guarda.total_presencas < semanas-4:
            enviar_email_baixa_frequencia(frequencia.guarda)

        messages.success(request, "Frequência registrada.")
        return redirect("mirim:frequencia_create")

    return render(request, "mirim/frequencias_form.html", {"form": form})

@group_required('super','Mirim_adm')
def checkin_evento(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    form = CheckinMatriculaForm(request.POST or None)

    if form.is_valid():
        matricula = form.cleaned_data["matricula"]

        try:
            guarda = GuardaMirim.objects.get(matricula=matricula)
        except GuardaMirim.DoesNotExist:
            messages.error(request, "Guarda não encontrado.")
            return redirect("mirim:checkin_evento", evento_id=evento.id)

        if Frequencia.objects.filter(guarda=guarda, evento=evento).exists():
            messages.error(request, "Presença já registrada.")
            return redirect("mirim:checkin_evento", evento_id)

        frequencia = Frequencia.objects.create(
            guarda=guarda,
            evento=evento,
            registrado_por_reconhecimento_facial=False,
        )

        enviar_email_participacao(guarda, evento)

        if guarda.total_presencas < 40:
            enviar_email_baixa_frequencia(guarda)

        messages.success(request, f"Presença registrada para {guarda.nome}.")
        return redirect("mirim:checkin_evento", evento_id)

    return render(request, "mirim/checkin.html", {"form": form, "e":evento})

@group_required('super','Mirim_adm')
def categoria_update(request, pk):
    categoria = get_object_or_404(CategoriaEvento, pk=pk)
    form = CategoriaEventoForm(request.POST or None, instance=categoria)

    if form.is_valid():
        form.save()
        messages.success(request, "Categoria atualizada com sucesso.")
        return redirect("mirim:categoria_list")

    return render(request, "mirim/categorias_form.html", {"form": form})

@group_required('super','Mirim_adm')
def local_update(request, pk):
    local = get_object_or_404(Local, pk=pk)
    form = LocalForm(request.POST or None, instance=local)

    if form.is_valid():
        form.save()
        messages.success(request, "Local atualizado com sucesso.")
        return redirect("mirim:local_list")

    return render(request, "mirim/locais_form.html", {"form": form})

@group_required('super','Mirim_adm')
def local_update(request, pk):
    local = get_object_or_404(Local, pk=pk)
    form = LocalForm(request.POST or None, instance=local)

    if form.is_valid():
        form.save()
        messages.success(request, "Local atualizado com sucesso.")
        return redirect("mirim:local_list")

    return render(request, "mirim/locais_form.html", {"form": form})

@group_required('super','Mirim_adm')
def evento_update(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    form = EventoForm(request.POST or None, instance=evento)

    if form.is_valid():
        form.save()
        messages.success(request, "Evento atualizado com sucesso.")
        return redirect("mirim:evento_list")

    return render(request, "mirim/eventos_form.html", {"form": form})

@group_required('super','Mirim_adm')
def guarda_update(request, pk):
    guarda = get_object_or_404(GuardaMirim, pk=pk)
    form = GuardaMirimForm(request.POST or None, request.FILES or None, instance=guarda)

    if form.is_valid():
        form.save()
        messages.success(request, "Guarda atualizado com sucesso.")
        return redirect("mirim:guarda_list")

    return render(request, "mirim/mirim_form.html", {"form": form})

@group_required('super','Mirim_adm')
@require_POST
def delete_object(request):
    model = request.POST.get("model")
    pk = request.POST.get("pk")

    models_map = {
        "categoria": CategoriaEvento,
        "local": Local,
        "mirim": GuardaMirim,
        "evento": Evento,
    }

    ModelClass = models_map.get(model)

    if not ModelClass:
        messages.error(request, "Registro não excluído. Modelo inválido.")
        return redirect("mirim:"+model+"_list")

    obj = get_object_or_404(ModelClass, pk=pk)
    obj.delete()

    messages.success(request, "Registro excluído com sucesso.")
    return redirect("mirim:"+model+"_list")

def mirim_consulta(request):
    if request.method == "POST":
        matricula = request.POST.get("matricula")
        cpf = request.POST.get("cpf")

        try:
            guarda = GuardaMirim.objects.get(matricula=matricula, cpf=cpf)
        except GuardaMirim.DoesNotExist:
            messages.error(request, "Dados inválidos.")
            return redirect("mirim:consulta")

        # salva na sessão
        request.session["guarda_id"] = guarda.id

        return redirect("mirim:mirim_detail_logado")

    return render(request, "mirim/consulta.html")

def _dados_guarda_detail(guarda):
    frequencias = (
        guarda.frequencias
        .select_related("evento", "evento__categoria", "evento__local")
        .order_by("-evento__data", "-evento__hora")
    )

    resumo_categorias = (
        guarda.frequencias
        .values("evento__categoria__nome")
        .annotate(total=Count("id"))
        .order_by("evento__categoria__nome")
    )

    # cor da barra baseada no status
    if guarda.status_aptidao == "Apto":
        cor_barra = "bg-guarda-mirim"
    elif guarda.status_aptidao == "Frequência constante":
        cor_barra = "bg-success"
    else:
        cor_barra = "bg-danger"

    return frequencias, resumo_categorias, cor_barra


@group_required('super','Mirim_adm')
def guarda_detail(request, pk):
    guarda = get_object_or_404(GuardaMirim, pk=pk)

    ano = request.GET.get("ano")

    # 🔥 pega o círio correto
    if ano:
        cirio = get_object_or_404(Cirio, ano=ano)
    else:
        cirio = Cirio.objects.filter(ativo=True).first()

    # 🔥 frequências dentro do período do círio
    frequencias = (
        guarda.frequencias
        .filter(evento__data__range=(cirio.inicio, cirio.termino))
        .select_related("evento", "evento__categoria", "evento__local")
        .order_by("-evento__data")
    )

    # 🔥 resumo simples
    resumo_categorias = (
        frequencias
        .values("evento__categoria__id", "evento__categoria__nome")
        .annotate(total=Count("id"))
        .order_by("evento__categoria__nome")
    )

    # 🔥 PROGRESSO POR REGRA (ESSENCIAL)
    from datetime import date
    hoje = date.today()

    # =========================
    # 🔥 TEMPO DO CÍRIO
    # =========================
    total_dias = (cirio.termino - cirio.inicio).days
    dias_passados = (min(hoje, cirio.termino) - cirio.inicio).days

    semanas_totais = total_dias / 7 if total_dias > 0 else 1
    semanas_passadas = max(dias_passados / 7, 0)

    # =========================
    # 🔥 PROGRESSO POR CATEGORIA
    # =========================
    progresso = []
    status_categoria = []

    for regra in cirio.regras.select_related("categoria"):

        total = frequencias.filter(
            evento__categoria=regra.categoria
        ).count()

        necessario = regra.quantidade_necessaria

        # 🔥 esperado até hoje
        esperado = (semanas_passadas / semanas_totais) * necessario

        percentual = 0
        if necessario > 0:
            percentual = min((total / necessario) * 100, 100)

        progresso.append({
            "categoria": regra.categoria.nome,
            "total": total,
            "necessario": necessario,
            "percentual": percentual,
            "esperado": esperado,
        })

        # =========================
        # 🔥 STATUS POR CATEGORIA
        # =========================
        if total >= necessario:
            status_categoria.append("apto")

        elif total >= esperado:
            status_categoria.append("tendencia")

        elif total < (esperado * 0.5):
            status_categoria.append("critico")

        else:
            status_categoria.append("baixo")

    # =========================
    # 🔥 STATUS FINAL
    # =========================
    if all(p["total"] >= p["necessario"] for p in progresso if p["necessario"] > 0):
        status = "APTO"

    elif hoje > cirio.termino:
        status = "INAPTO"

    elif any(s == "critico" for s in status_categoria):
        status = "ABAIXO DE 50% DA TENDÊNCIA"

    elif all(s in ["apto", "tendencia"] for s in status_categoria):
        status = "TENDÊNCIA"

    else:
        status = "ABAIXO DO ESPERADO"

        # 🔥 STATUS APTO DINÂMICO
        apto = all(p["total"] >= p["necessario"] for p in progresso if p["necessario"] > 0)

    cirios = Cirio.objects.all().order_by("ano")

    return render(request, "mirim/mirim_detail.html", {
        "guarda": guarda,
        "frequencias": frequencias,
        "resumo_categorias": resumo_categorias,
        "progresso": progresso,
        "cirio": cirio,
        "status": status,
        "cirios": cirios,
    })


def mirim_detail_consulta(request):
    guarda_id = request.session.get("guarda_id")

    if not guarda_id:
        return redirect("mirim:consulta")

    guarda = get_object_or_404(GuardaMirim, id=guarda_id)

    ano = request.GET.get("ano")

    # 🔥 pega o círio correto
    if ano:
        cirio = get_object_or_404(Cirio, ano=ano)
    else:
        cirio = Cirio.objects.filter(ativo=True).first()

    # 🔥 frequências dentro do período do círio
    frequencias = (
        guarda.frequencias
        .filter(evento__data__range=(cirio.inicio, cirio.termino))
        .select_related("evento", "evento__categoria", "evento__local")
        .order_by("-evento__data")
    )

    # 🔥 resumo simples
    resumo_categorias = (
        frequencias
        .values("evento__categoria__id", "evento__categoria__nome")
        .annotate(total=Count("id"))
        .order_by("evento__categoria__nome")
    )

    # 🔥 PROGRESSO POR REGRA (ESSENCIAL)
    from datetime import date
    hoje = date.today()

    # =========================
    # 🔥 TEMPO DO CÍRIO
    # =========================
    total_dias = (cirio.termino - cirio.inicio).days
    dias_passados = (min(hoje, cirio.termino) - cirio.inicio).days

    semanas_totais = total_dias / 7 if total_dias > 0 else 1
    semanas_passadas = max(dias_passados / 7, 0)

    # =========================
    # 🔥 PROGRESSO POR CATEGORIA
    # =========================
    progresso = []
    status_categoria = []

    for regra in cirio.regras.select_related("categoria"):

        total = frequencias.filter(
            evento__categoria=regra.categoria
        ).count()

        necessario = regra.quantidade_necessaria

        # 🔥 esperado até hoje
        esperado = (semanas_passadas / semanas_totais) * necessario

        percentual = 0
        if necessario > 0:
            percentual = min((total / necessario) * 100, 100)

        progresso.append({
            "categoria": regra.categoria.nome,
            "total": total,
            "necessario": necessario,
            "percentual": percentual,
            "esperado": esperado,
        })

        # =========================
        # 🔥 STATUS POR CATEGORIA
        # =========================
        if total >= necessario:
            status_categoria.append("apto")

        elif total >= esperado:
            status_categoria.append("tendencia")

        elif total < (esperado * 0.5):
            status_categoria.append("critico")

        else:
            status_categoria.append("baixo")

    # =========================
    # 🔥 STATUS FINAL
    # =========================
    if all(p["total"] >= p["necessario"] for p in progresso if p["necessario"] > 0):
        status = "APTO"

    elif hoje > cirio.termino:
        status = "INAPTO"

    elif any(s == "critico" for s in status_categoria):
        status = "ABAIXO DE 50% DA TENDÊNCIA"

    elif all(s in ["apto", "tendencia"] for s in status_categoria):
        status = "TENDÊNCIA"

    else:
        status = "ABAIXO DO ESPERADO"

        # 🔥 STATUS APTO DINÂMICO
        apto = all(p["total"] >= p["necessario"] for p in progresso if p["necessario"] > 0)

    cirios = Cirio.objects.all().order_by("ano")

    return render(request, "mirim/mirim_detail.html", {
        "guarda": guarda,
        "frequencias": frequencias,
        "resumo_categorias": resumo_categorias,
        "progresso": progresso,
        "cirio": cirio,
        "status": status,
        "cirios": cirios,
    })

@login_required
def guarda_consulta(request, pk):
    guarda = get_object_or_404(GuardaMirim, pk=pk)
    context = {
        "guarda": guarda,
    }
    return render(request, "mirim/mirim_consulta.html", context)

@login_required
def cirio_list(request):
    cirios = Cirio.objects.all()
    return render(request, "mirim/cirio_list.html", {"cirios": cirios})

@login_required
def cirio_form(request, pk=None):
    cirio = get_object_or_404(Cirio, pk=pk) if pk else None

    extra_forms = int(request.POST.get("extra_forms", 1))

    RegraFormSet = inlineformset_factory(
        Cirio,
        RegraCirio,
        fields=("categoria", "quantidade_necessaria"),
        extra=extra_forms,
        can_delete=True
    )

    if request.method == "POST":
        if "add_regra" in request.POST:
            # usuário clicou em adicionar regra
            form = CirioForm(request.POST, instance=cirio)
            formset = RegraFormSet(request.POST, instance=cirio)
            extra_forms += 1

            RegraFormSet = inlineformset_factory(
                Cirio,
                RegraCirio,
                fields=("categoria", "quantidade_necessaria"),
                extra=extra_forms,
                can_delete=True
            )

            formset = RegraFormSet(instance=cirio)

            return render(request, "mirim/cirio_form.html", {
                "form": form,
                "formset": formset,
                "extra_forms": extra_forms,
                "cirio": cirio
            })

        form = CirioForm(request.POST, instance=cirio)
        formset = RegraFormSet(request.POST, instance=cirio)

        print("FORM VALID:", form.is_valid())
        print("FORMSET VALID:", formset.is_valid())
        print(form.errors)
        print(formset.errors)
        if form.is_valid() and formset.is_valid():
            cirio = form.save()
            formset.instance = cirio
            formset.save()

            messages.success(request, "Círio salvo com sucesso.")
            return redirect("mirim:cirio_list")

    else:
        form = CirioForm(instance=cirio)
        formset = RegraFormSet(instance=cirio)

    return render(request, "mirim/cirio_form.html", {
        "form": form,
        "formset": formset,
        "extra_forms": extra_forms,
        "cirio": cirio
    })
@login_required
def cirio_detail(request, pk):
    cirio = get_object_or_404(Cirio, pk=pk)
    regras = cirio.regras.select_related("categoria")

    return render(request, "mirim/cirio_detail.html", {
        "cirio": cirio,
        "regras": regras
    })

@require_POST
@login_required
def cirio_delete(request, pk):
    cirio = get_object_or_404(Cirio, pk=pk)
    cirio.delete()

    messages.success(request, "Círio excluído com sucesso.")
    return redirect("mirim:cirio_list")
