from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "categoria"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Setor(models.Model):
    nome = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=150, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "setor"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Material(models.Model):
    STATUS_CHOICES = [
        ("disponivel", "Disponível"),
        ("indisponivel", "Indisponível"),
        ("manutencao", "Em manutenção"),
        ("defeito", "Com defeito"),
        ("problema", "Com problemas"),
    ]

    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    numero_patrimonio = models.CharField(max_length=50, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="disponivel")
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    qtd_disponivel = models.IntegerField(default=0)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Estoque(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="estoques")
    quantidade = models.IntegerField(default=0)
    validade = models.DateField(blank=True, null=True)
    local_provisorio = models.CharField(max_length=150, blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Estoque de {self.material.nome}"


class Emprestimo(models.Model):
    STATUS_CHOICES = [
        ("solicitado", "Solicitado"),
        ("aprovado", "Aprovado"),
        ("retirado", "Retirado"),
        ("devolvido", "Devolvido"),
        ("atrasado", "Atrasado"),
        ("cancelado", "Cancelado"),
    ]

    material = models.ForeignKey(Material, on_delete=models.PROTECT)

    solicitante = models.ForeignKey(
        "app.Guarda",
        on_delete=models.PROTECT,
        related_name="emprestimos_solicitados",
    )

    retirante = models.ForeignKey(
        "app.Guarda",
        on_delete=models.PROTECT,
        related_name="emprestimos_retirados",
        blank=True,
        null=True,
    )

    responsavel_patrimonio = models.ForeignKey(
        "app.Guarda",
        on_delete=models.PROTECT,
        related_name="emprestimos_liberados",
        blank=True,
        null=True,
    )

    quantidade = models.IntegerField(default=0)
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_retirada = models.DateTimeField(blank=True, null=True)
    data_devolucao = models.DateTimeField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="solicitado")
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.material.nome} - {self.status}"