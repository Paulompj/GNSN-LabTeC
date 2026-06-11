from django.db import models


class CategoriaMaterial(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    descricao = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "CATEGORIA_MATERIAL"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Setor(models.Model):
    nome = models.CharField(max_length=200)
    localizacao = models.CharField(max_length=200, blank=True, null=True)
    is_ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "SETOR"
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

    categoria = models.ForeignKey(CategoriaMaterial, on_delete=models.PROTECT)
    setor = models.ForeignKey(
        Setor, on_delete=models.SET_NULL, null=True, blank=True
    )
    nome = models.CharField(max_length=200)
    numero_patrimonio = models.CharField(
        max_length=50, unique=True, blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="disponivel"
    )
    qtd_disponivel = models.IntegerField(default=0)
    data_cadastro = models.DateField(auto_now_add=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "MATERIAL"

    def __str__(self):
        return self.nome


class Estoque(models.Model):
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name="estoques"
    )
    quantidade = models.IntegerField(default=0)
    validade = models.DateField(blank=True, null=True)
    local_provisorio = models.CharField(max_length=200, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ESTOQUE"

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
        "guarda.Guarda",
        on_delete=models.PROTECT,
        related_name="emprestimos_solicitados",
    )
    retirante = models.ForeignKey(
        "guarda.Guarda",
        on_delete=models.PROTECT,
        related_name="emprestimos_retirados",
        blank=True,
        null=True,
    )
    responsavel_patrimonio = models.ForeignKey(
        "guarda.Guarda",
        on_delete=models.PROTECT,
        related_name="emprestimos_liberados",
        blank=True,
        null=True,
    )
    quantidade = models.IntegerField(default=0)
    data_solicitacao = models.DateField(auto_now_add=True)
    data_retirada = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="solicitado"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "EMPRESTIMO"

    def __str__(self):
        return f"{self.material.nome} - {self.status}"
