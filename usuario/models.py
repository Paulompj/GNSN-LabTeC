from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UsuarioManager(BaseUserManager):
    def create_user(self, usuario, password=None, **extra_fields):
        if not usuario:
            raise ValueError("O nome de usuário é obrigatório")
        user = self.model(usuario=usuario, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, usuario, password=None, **extra_fields):
        extra_fields.setdefault("is_super_usuario", True)
        extra_fields.setdefault("is_funcionario", True)
        extra_fields.setdefault("is_ativo", True)
        return self.create_user(usuario, password, **extra_fields)


class Usuario(AbstractBaseUser):
    pessoa = models.OneToOneField(
        "pessoa.Pessoa", on_delete=models.CASCADE, related_name="usuario"
    )
    usuario = models.CharField(max_length=50, unique=True)
    # A senha é armazenada no campo `password` herdado de AbstractBaseUser
    is_funcionario = models.BooleanField(default=False)
    is_super_usuario = models.BooleanField(default=False)
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

    @property
    def is_superuser(self):
        return self.is_super_usuario

    def has_perm(self, perm, obj=None):
        return self.is_super_usuario

    def has_module_perms(self, app_label):
        return self.is_super_usuario
