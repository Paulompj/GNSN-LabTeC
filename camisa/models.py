from django.db import models
import os

from guarda.models import Guarda, GuardaApoio

apto = ["INAPTO", "APTO"]
recebeu = ["NÃO RECEBIDO", "RECEBIDO"]


def termo_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]  # pega extensão
    newname = f"{instance.ano}-{instance.guarda.matricula}{ext}"
    return os.path.join("termos/", newname)


def procuracao_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    newname = f"{instance.ano}-{instance.guarda.matricula}-proc{ext}"
    return os.path.join("procuracoes/", newname)


class Camisa(models.Model):
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
    ano = models.IntegerField()
    guarda = models.ForeignKey(
        Guarda, on_delete=models.DO_NOTHING, related_name="camisas_recebidas"
    )
    equipe = models.CharField(max_length=15)
    situacao = models.BooleanField()  # tinyint -> boolean
    tamcamisa = models.CharField(max_length=2, choices=TAMANHOS)
    recebido = models.BooleanField()
    arquivo = models.ImageField(upload_to=termo_upload_path, blank=True, null=True)
    procuracao = models.FileField(
        upload_to=procuracao_upload_path, blank=True, null=True
    )  # novo campo
    recebedor = models.CharField(max_length=45, null=True, blank=True)
    entregador = models.ForeignKey(
        Guarda, on_delete=models.DO_NOTHING, related_name="camisas_entregues"
    )
    criador = models.ForeignKey(
        Guarda, on_delete=models.DO_NOTHING, related_name="camisas_criadas"
    )
    data = models.DateTimeField()

    def __str__(self):
        return (
            str(self.guarda.nome)
            + " - "
            + str(self.ano)
            + " - "
            + self.tamcamisa
            + " - "
            + apto[self.situacao]
            + " - "
            + recebeu[self.recebido]
        )

    class Meta:
        db_table = "camisa"


class CamisaLog(models.Model):
    camisa = models.ForeignKey(Camisa, on_delete=models.CASCADE, related_name="logs")
    usuario = models.ForeignKey(Guarda, on_delete=models.CASCADE, null=True, blank=True)
    tamanho_antigo = models.CharField(max_length=5)
    tamanho_novo = models.CharField(max_length=5)
    situacao_antiga = models.CharField(max_length=10)  # "APTO" ou "INAPTO"
    situacao_nova = models.CharField(max_length=10)
    equipe_antiga = models.CharField(
        max_length=15, null=True, blank=True
    )  # <-- novo campo
    equipe_nova = models.CharField(
        max_length=15, null=True, blank=True
    )  # <-- novo campo
    justificativa = models.CharField(max_length=50, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Camisa {self.camisa.id}: "
            f"{self.tamanho_antigo} → {self.tamanho_novo}, "
            f"{self.situacao_antiga} → {self.situacao_nova}, "
            f"{self.equipe_antiga} → {self.equipe_nova} "
            f"por {self.usuario.nome if self.usuario else 'Usuário não informado'}"
        )

    class Meta:
        db_table = "camisa_log"
        ordering = ["-data_alteracao"]


class CamisaGuardaApoio(models.Model):
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

    apoio = models.ForeignKey(
        GuardaApoio, on_delete=models.CASCADE, related_name="camisas"
    )
    tamanho = models.CharField(max_length=2, choices=TAMANHOS)
    quantidade = models.PositiveIntegerField(default=0)
    recebido = models.BooleanField(default=False)
    entregador = models.ForeignKey(
        Guarda,
        on_delete=models.DO_NOTHING,
        related_name="apoio_entregues",
        null=True,
        blank=True,
    )
    observacao = models.TextField(null=True, blank=True)
    data = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            "apoio",
            "tamanho",
        )  # evita duplicidade de tamanho para o mesmo guarda

    def __str__(self):
        return f"{self.apoio} - {self.tamanho}: {self.quantidade}"
