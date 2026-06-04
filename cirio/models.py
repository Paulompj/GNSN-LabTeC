from django.db import models


class Cirio(models.Model):
    ano = models.PositiveIntegerField(unique=True)
    ativo = models.BooleanField(default=True)
    inicio = models.DateField()
    termino = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CIRIO"
        ordering = ["-ano"]
        verbose_name = "Círio"
        verbose_name_plural = "Círios"

    def __str__(self):
        return f"Círio {self.ano}"


class CategoriaCirio(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "CATEGORIA_CIRIO"
        verbose_name = "Categoria do Círio"
        verbose_name_plural = "Categorias do Círio"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class RegraCirio(models.Model):
    cirio = models.ForeignKey(Cirio, on_delete=models.CASCADE, related_name="regras")
    categoria = models.ForeignKey(CategoriaCirio, on_delete=models.PROTECT)
    quantidade_necessaria = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "REGRA_CIRIO"
        unique_together = ("cirio", "categoria")
        verbose_name = "Regra do Círio"
        verbose_name_plural = "Regras do Círio"

    def __str__(self):
        return f"{self.categoria} - {self.quantidade_necessaria} ({self.cirio})"
