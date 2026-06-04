from django.db import models
from datetime import date

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
    guarda = models.ForeignKey('guarda.Guarda', on_delete=models.CASCADE, related_name="frequencias")
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