from django.db import models
from datetime import date
from django.core.validators import MinValueValidator, MaxValueValidator


class CategoriaEvento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoria de Evento"
        verbose_name_plural = "Categorias de Evento"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Local(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locais"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class GuardaMirim(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    endereco = models.TextField(blank=True)
    cpf = models.CharField(max_length=14, unique=True)
    matricula = models.CharField(max_length=20, unique=True)

    foto = models.ImageField(upload_to="mirim/fotos/", blank=True, null=True)

    responsavel_nome = models.CharField(max_length=200, blank=True)
    responsavel_contato = models.CharField(max_length=50, blank=True)
    parentesco_responsavel = models.CharField(
        max_length=10,
        choices=[("Pai", "Pai"), ("Mãe", "Mãe"), ("Outro", "Outro")],
        blank=True,
    )

    # Novos campos
    data_nascimento = models.DateField(null=True, blank=True)
    tamanho_camisa = models.CharField(
        max_length=3,
        choices=[("PP", "PP"), ("P", "P"), ("M", "M"), ("G", "G"), ("GG", "GG")],
        blank=True,
    )

    # Saúde / necessidades especiais
    autismo_tdah_alergia = models.CharField(max_length=200, blank=True)
    intolerancia_alimentar = models.CharField(max_length=200, blank=True)
    doenca_cronica = models.CharField(max_length=200, blank=True)
    uso_medicamento_controlado = models.CharField(max_length=200, blank=True)
    observacoes_pais = models.TextField(blank=True)

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Guarda Mirim"
        verbose_name_plural = "Guardas Mirins"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.matricula})"

    @property
    def total_presencas(self):
        return self.frequencias.filter(evento__categoria__nome="Missa").count()

    @property
    def progresso_percentual(self):
        return min((self.total_presencas / 52) * 100, 100)

    @property
    def status_aptidao(self):
        hoje = date.today()
        inicio = date(hoje.year, 9, 1)
        if hoje < inicio:
            inicio = date(hoje.year - 1, 9, 1)
        semanas = (hoje - inicio).days // 7
        if self.total_presencas >= 52:
            return "Apto"
        elif self.total_presencas >= semanas:
            return "Frequência constante"
        return "Frequência baixa"

    def progresso_por_cirio(self, cirio):
        progresso = []

        for regra in cirio.regras.all():
            total = self.frequencias.filter(
                evento__categoria=regra.categoria,
                evento__data__range=(cirio.inicio, cirio.termino)
            ).count()

            progresso.append({
                "categoria": regra.categoria.nome,
                "feito": total,
                "necessario": regra.quantidade_necessaria,
                "ok": total >= regra.quantidade_necessaria
            })

        return progresso

    def status_no_cirio(self, cirio):
        for regra in cirio.regras.all():
            total = self.frequencias.filter(
                evento__categoria=regra.categoria,
                evento__data__range=(cirio.inicio, cirio.termino)
            ).count()

            if total < regra.quantidade_necessaria:
                return "Inapto"

        return "Apto"


class Evento(models.Model):
    categoria = models.ForeignKey(CategoriaEvento, on_delete=models.PROTECT, related_name="eventos")
    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name="eventos")

    data = models.DateField()
    hora = models.TimeField()

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-data", "-hora"]
        unique_together = ("categoria", "local", "data", "hora")

    def __str__(self):
        return f"{self.categoria} - {self.local} - {self.data} {self.hora}"


class Frequencia(models.Model):
    guarda = models.ForeignKey(GuardaMirim, on_delete=models.CASCADE, related_name="frequencias")
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="frequencias")

    data_registro = models.DateTimeField(auto_now_add=True)

    registrado_por_reconhecimento_facial = models.BooleanField(default=False)
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = "Frequência"
        verbose_name_plural = "Frequências"
        unique_together = ("guarda", "evento")
        ordering = ["-data_registro"]

    def __str__(self):
        return f"{self.guarda} - {self.evento}"

class Cirio(models.Model):
    ano = models.PositiveIntegerField(unique=True)
    inicio = models.DateField()
    termino = models.DateField()
    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ano"]
        verbose_name = "Círio"
        verbose_name_plural = "Círios"

    def __str__(self):
        return f"Círio {self.ano}"

class RegraCirio(models.Model):
    cirio = models.ForeignKey(Cirio, on_delete=models.CASCADE, related_name="regras")
    categoria = models.ForeignKey(CategoriaEvento, on_delete=models.PROTECT)

    quantidade_necessaria = models.PositiveIntegerField()

    class Meta:
        unique_together = ("cirio", "categoria")
        verbose_name = "Regra do Círio"
        verbose_name_plural = "Regras do Círio"

    def __str__(self):
        return f"{self.categoria} - {self.quantidade_necessaria} ({self.cirio})"