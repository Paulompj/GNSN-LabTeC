from django.db import models


class Pessoa(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=50, null=True, blank=True)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    rg = models.CharField(max_length=45, unique=True, null=True, blank=True)
    estado_civil = models.CharField(max_length=50, null=True, blank=True)
    genero = models.CharField(max_length=50, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "PESSOA"

    def __str__(self):
        return self.nome


class Endereco(models.Model):
    pessoa = models.OneToOneField(
        Pessoa, on_delete=models.CASCADE, related_name="endereco"
    )
    logradouro = models.CharField(max_length=200, null=True, blank=True)
    complemento = models.CharField(max_length=200, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cep = models.CharField(max_length=20, null=True, blank=True)
    uf = models.CharField(max_length=10, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ENDERECO"

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.cidade}"
