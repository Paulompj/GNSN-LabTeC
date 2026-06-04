from django.db import models


TAMANHOS = [
    ("PP", "PP"),
    ("P", "P"),
    ("M", "M"),
    ("G", "G"),
    ("GG", "GG"),
    ("3G", "3G"),
    ("4G", "4G"),
    ("5G", "5G"),
    ("6G", "6G"),
]


class Equipe(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "EQUIPE"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Camisa(models.Model):
    equipe = models.ForeignKey(
        Equipe, on_delete=models.PROTECT, related_name="camisas"
    )
    guarda = models.ForeignKey(
        "guarda.Guarda", on_delete=models.PROTECT, related_name="camisas_recebidas"
    )
    entregador = models.ForeignKey(
        "guarda.Guarda",
        on_delete=models.PROTECT,
        related_name="camisas_entregues",
        null=True,
        blank=True,
    )
    criador = models.ForeignKey(
        "guarda.Guarda",
        on_delete=models.PROTECT,
        related_name="camisas_criadas",
        null=True,
        blank=True,
    )
    ano = models.IntegerField()
    tamanho_camisa = models.CharField(max_length=10, choices=TAMANHOS)
    situacao = models.BooleanField(default=False)
    recebido = models.BooleanField(default=False)
    recebedor = models.CharField(max_length=200, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CAMISA"

    def __str__(self):
        return f"{self.guarda.nome} - {self.ano} - {self.tamanho_camisa}"


class CamisaLog(models.Model):
    camisa = models.ForeignKey(Camisa, on_delete=models.CASCADE, related_name="logs")
    usuario = models.ForeignKey(
        "usuario.Usuario", on_delete=models.SET_NULL, null=True, blank=True
    )
    tamanho_antigo = models.CharField(max_length=10, null=True, blank=True)
    tamanho_novo = models.CharField(max_length=10, null=True, blank=True)
    situacao_antiga = models.BooleanField(null=True, blank=True)
    situacao_nova = models.BooleanField(null=True, blank=True)
    justificativa = models.CharField(max_length=200, null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "CAMISA_LOG"
        ordering = ["-data_alteracao"]

    def __str__(self):
        return (
            f"Camisa {self.camisa_id}: "
            f"{self.tamanho_antigo} → {self.tamanho_novo}"
        )
