from django.db import models


class CategoriaEvento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    is_ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CATEGORIA_EVENTO"
        verbose_name = "Categoria de Evento"
        verbose_name_plural = "Categorias de Evento"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Local(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    is_ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "LOCAL"
        verbose_name = "Local"
        verbose_name_plural = "Locais"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Evento(models.Model):
    categoria = models.ForeignKey(
        CategoriaEvento, on_delete=models.PROTECT, related_name="eventos"
    )
    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name="eventos")
    data = models.DateField()
    hora = models.TimeField()
    is_frequencia_autorizada = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "EVENTO"
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-data", "-hora"]
        unique_together = ("categoria", "local", "data", "hora")

    def __str__(self):
        return f"{self.categoria} - {self.local} - {self.data} {self.hora}"


class Frequencia(models.Model):
    guarda = models.ForeignKey(
        "guarda.Guarda", on_delete=models.CASCADE, related_name="frequencias"
    )
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="frequencias"
    )
    data_registro = models.DateField(auto_now_add=True)
    hora_registro = models.DateTimeField(auto_now_add=True)
    reconhecimento_facial = models.BooleanField(default=False)
    observacao = models.CharField(max_length=250, null=True, blank=True)

    class Meta:
        db_table = "FREQUENCIA"
        verbose_name = "Frequência"
        verbose_name_plural = "Frequências"
        unique_together = ("guarda", "evento")
        ordering = ["-data_registro"]

    def __str__(self):
        return f"{self.guarda} - {self.evento}"
