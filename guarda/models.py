from django.db import models


class Guarda(models.Model):
    pessoa = models.OneToOneField(
        "pessoa.Pessoa", on_delete=models.CASCADE, related_name="guarda"
    )
    turma = models.IntegerField(null=True, blank=True)
    tipo = models.CharField(max_length=20, null=True, blank=True)
    ministerio = models.CharField(max_length=50, null=True, blank=True)
    paroquia = models.CharField(max_length=200, null=True, blank=True)
    matricula = models.CharField(max_length=20, unique=True)
    tamanho_camisa = models.CharField(max_length=10, null=True, blank=True)
    observacao = models.CharField(max_length=200, null=True, blank=True)
    data_ingresso = models.DateField(null=True, blank=True)
    is_ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "GUARDA"

    def __str__(self):
        return f"{self.matricula} - {self.pessoa.nome}"

    @property
    def nome(self):
        return self.pessoa.nome

    @property
    def email(self):
        return self.pessoa.email

    @property
    def cpf(self):
        return self.pessoa.cpf

    @property
    def data_nascimento(self):
        return self.pessoa.data_nascimento

    @property
    def endereco(self):
        return (
            self.pessoa.endereco.logradouro
            if hasattr(self.pessoa, "endereco")
            else ""
        )

    @property
    def responsavel_nome(self):
        resp = self.responsaveis.first()
        return resp.pessoa.nome if resp else ""

    @property
    def responsavel_contato(self):
        resp = self.responsaveis.first()
        return resp.pessoa.telefone if resp else ""

    @property
    def parentesco_responsavel(self):
        resp = self.responsaveis.first()
        return resp.parentesco if resp else ""

    @property
    def total_presencas(self):
        return self.frequencias.filter(evento__categoria__nome="Missa").count()

    @property
    def progresso_percentual(self):
        return min((self.total_presencas / 52) * 100, 100)

    @property
    def status_aptidao(self):
        from datetime import date

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
                evento__data__range=(cirio.inicio, cirio.termino),
            ).count()
            progresso.append(
                {
                    "categoria": regra.categoria.nome,
                    "feito": total,
                    "necessario": regra.quantidade_necessaria,
                    "ok": total >= regra.quantidade_necessaria,
                }
            )
        return progresso


class StatusGuarda(models.Model):
    nome = models.CharField(max_length=100)
    is_temporario = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "STATUS_GUARDA"

    def __str__(self):
        return self.nome


class GuardaStatus(models.Model):
    guarda = models.ForeignKey(
        Guarda, on_delete=models.CASCADE, related_name="status_historico"
    )
    status = models.ForeignKey(StatusGuarda, on_delete=models.PROTECT)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    motivo = models.CharField(max_length=200, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "GUARDA_STATUS"

    def __str__(self):
        return f"{self.guarda} - {self.status}"


class Sacramento(models.Model):
    guarda = models.OneToOneField(
        Guarda, on_delete=models.CASCADE, related_name="sacramento"
    )
    batismo = models.BooleanField(default=False)
    primeira_eucaristia = models.BooleanField(default=False)
    crisma = models.BooleanField(default=False)
    ordem = models.BooleanField(default=False)
    data_batismo = models.DateField(null=True, blank=True)
    data_primeira_eucaristia = models.DateField(null=True, blank=True)
    data_crisma = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "SACRAMENTO"

    def __str__(self):
        return f"Sacramentos - {self.guarda}"


class ResponsavelGuarda(models.Model):
    guarda = models.ForeignKey(
        Guarda, on_delete=models.CASCADE, related_name="responsaveis"
    )
    pessoa = models.ForeignKey("pessoa.Pessoa", on_delete=models.CASCADE)
    parentesco = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "RESPONSAVEL_GUARDA"
        unique_together = (("guarda", "pessoa"),)


class PadrinhoGuarda(models.Model):
    guarda = models.ForeignKey(
        Guarda, on_delete=models.CASCADE, related_name="padrinhos"
    )
    padrinho = models.ForeignKey(
        Guarda, on_delete=models.CASCADE, related_name="afilhados"
    )

    class Meta:
        db_table = "PADRINHO_GUARDA"
        unique_together = (("guarda", "padrinho"),)
