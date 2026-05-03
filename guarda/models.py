import os
from django.db import models

# from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def foto_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    new_name = f"{instance.matricula}{ext}"
    return os.path.join("perfis/", new_name)


class GuardaManager(BaseUserManager):
    def create_user(self, matricula, password=None, **extra_fields):
        if not matricula:
            raise ValueError("O número de matrícula é obrigatório")
        user = self.model(matricula=matricula, **extra_fields)
        user.set_password(password)  # criptografa a senha
        user.save(using=self._db)
        return user

    def create_superuser(self, matricula, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(matricula, password, **extra_fields)


class Guarda(AbstractBaseUser, PermissionsMixin):
    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]

    ESTADO_CIVIL_CHOICES = [
        ("solteiro", "Solteiro(a)"),
        ("casado", "Casado(a)"),
        ("separado", "Separado(a)"),
        ("divorciado", "Divorciado(a)"),
        ("viuvo", "Viúvo(a)"),
        ("uniao_estavel", "União Estável"),
    ]

    idguarda = models.AutoField(primary_key=True)  # INT NOT NULL PRIMARY KEY
    matricula = models.IntegerField(unique=True)
    turma = models.IntegerField(null=True, blank=True)
    matricula_padrinho = models.IntegerField(null=True, blank=True)
    nome = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    foto = models.ImageField(upload_to=foto_upload_path, blank=True, null=True)
    nascimento = models.DateField(null=True, blank=True)
    endereco = models.CharField(max_length=45, null=True, blank=True)
    cidade = models.CharField(max_length=45, null=True, blank=True)
    bairro = models.CharField(max_length=45, null=True, blank=True)
    cep = models.CharField(max_length=9, null=True, blank=True)
    cpf = models.CharField(max_length=15, null=True, blank=True)
    rg = models.CharField(max_length=45, null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, null=True, blank=True)
    estado_civil = models.CharField(
        max_length=20, choices=ESTADO_CIVIL_CHOICES, null=True, blank=True
    )
    telefone = models.CharField(max_length=45, null=True, blank=True)
    celular = models.CharField(max_length=45, null=True, blank=True)
    tel_comercial = models.CharField(max_length=45, null=True, blank=True)
    complemento = models.CharField(max_length=45, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)
    UF = models.CharField(max_length=2, null=True, blank=True)
    encoding = models.BinaryField(null=True, blank=True)
    must_change_password = models.BooleanField(default=True)  # força troca de senha

    USERNAME_FIELD = "matricula"
    REQUIRED_FIELDS = ["nome"]

    objects = GuardaManager()

    def __str__(self):
        return str(self.matricula) + " - " + self.nome

    class Meta:
        db_table = "Guarda"


class GuardaApoio(models.Model):
    matricula = models.CharField(max_length=7)
    responsavel = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    paroquia = models.CharField(max_length=255)
    telefone = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.responsavel} - {self.paroquia} - {self.municipio}"
