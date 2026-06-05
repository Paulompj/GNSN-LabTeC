from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UsuarioManager(BaseUserManager):
    def create_user(self, usuario, password=None, **extra_fields):
        if not usuario:
            raise ValueError("O nome de usuário é obrigatório")
        user = self.model(usuario=usuario, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, usuario, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_funcionario", True)
        extra_fields.setdefault("is_ativo", True)
        # USUARIO.pessoa_id é NOT NULL (diagrama). Se nenhuma Pessoa for
        # informada, cria uma automaticamente para o superusuário.
        if "pessoa" not in extra_fields and "pessoa_id" not in extra_fields:
            from pessoa.models import Pessoa

            extra_fields["pessoa"] = Pessoa.objects.create(nome=usuario)
        return self.create_user(usuario, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    pessoa = models.OneToOneField(
        "pessoa.Pessoa", on_delete=models.CASCADE, related_name="usuario"
    )
    usuario = models.CharField(max_length=50, unique=True)
    # A senha é armazenada no campo `password` herdado de AbstractBaseUser.
    # `is_superuser`, `groups` e `user_permissions` vêm do PermissionsMixin.
    is_funcionario = models.BooleanField(default=False)
    is_ativo = models.BooleanField(default=True)
    trocar_senha = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "usuario"

    objects = UsuarioManager()

    class Meta:
        db_table = "USUARIO"

    def __str__(self):
        return self.usuario

    # Compatibilidade com o sistema de autenticação/admin do Django
    @property
    def is_active(self):
        return self.is_ativo

    @property
    def is_staff(self):
        return self.is_funcionario
