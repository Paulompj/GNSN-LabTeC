import os
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

def foto_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    new_name = f"{instance.cpf}{ext}"
    return os.path.join("perfis/", new_name)

class Pessoa(models.Model):
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, null=True, blank=True)
    estado_civil = models.CharField(max_length=20, null=True, blank=True)
    nacionalidade = models.CharField(max_length=50, null=True, blank=True)
    naturalidade = models.CharField(max_length=50, null=True, blank=True)
    nome_pai = models.CharField(max_length=200, null=True, blank=True)
    nome_mae = models.CharField(max_length=200, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    celular = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    foto = models.ImageField(upload_to=foto_upload_path, blank=True, null=True)
    observacao = models.TextField(null=True, blank=True)
    is_ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "PESSOA"

    def __str__(self):
        return self.nome

class Endereco(models.Model):
    pessoa = models.OneToOneField(Pessoa, on_delete=models.CASCADE, related_name="endereco_obj")
    cep = models.CharField(max_length=10, null=True, blank=True)
    logradouro = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        db_table = "ENDERECO"

class FichaSaude(models.Model):
    guarda = models.OneToOneField('Guarda', on_delete=models.CASCADE)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    altura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    tipoSanguineo = models.CharField(max_length=5, null=True, blank=True)
    alergias = models.TextField(null=True, blank=True)
    doenca_cronica = models.TextField(null=True, blank=True)
    medicamento_continuo = models.TextField(null=True, blank=True)
    restricao_alimentar = models.TextField(null=True, blank=True)
    plano_saude = models.CharField(max_length=100, null=True, blank=True)
    contato_emergencia = models.CharField(max_length=100, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "FICHA_SAUDE"

class Sacramento(models.Model):
    guarda = models.OneToOneField('Guarda', on_delete=models.CASCADE)
    batismo = models.BooleanField(default=False)
    eucaristia = models.BooleanField(default=False)
    crisma = models.BooleanField(default=False)
    matrimonio = models.BooleanField(default=False)
    data_batismo = models.DateField(null=True, blank=True)
    data_eucaristia = models.DateField(null=True, blank=True)
    data_crisma = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "SACRAMENTO"

class GuardaManager(BaseUserManager):
    def create_user(self, matricula, password=None, **extra_fields):
        if not matricula:
            raise ValueError("A matrícula é obrigatória")
        user = self.model(matricula=matricula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matricula, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(matricula, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    pessoa = models.OneToOneField(Pessoa, on_delete=models.RESTRICT, null=True, blank=True)
    matricula = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)

    USERNAME_FIELD = "matricula"
    
    objects = GuardaManager()

    class Meta:
        db_table = "USUARIO"

class Guarda(models.Model):
    pessoa = models.OneToOneField(Pessoa, on_delete=models.RESTRICT)
    matricula = models.CharField(max_length=20, unique=True)
    data_ingresso = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Ativo')
    tipo = models.CharField(max_length=20)
    encoding = models.BinaryField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "GUARDA"

    def __str__(self):
        return f"{self.matricula} - {self.pessoa.nome}"

    @property
    def nome(self):
        return self.pessoa.nome

    @property
    def email(self):
        return self.pessoa.email

    @property
    def cpf(self):
        return self.pessoa.cpf

    @property
    def data_nascimento(self):
        return self.pessoa.data_nascimento

    @property
    def endereco(self):
        return self.pessoa.endereco_obj.logradouro if hasattr(self.pessoa, 'endereco_obj') else ""

    @property
    def responsavel_nome(self):
        resp = self.responsaveis.first()
        return resp.pessoa.nome if resp else ""

    @property
    def responsavel_contato(self):
        resp = self.responsaveis.first()
        return resp.pessoa.telefone if resp else ""

    @property
    def parentesco_responsavel(self):
        resp = self.responsaveis.first()
        return resp.parentesco if resp else ""

    @property
    def autismo_tdah_alergia(self):
        return self.fichasaude.alergias if hasattr(self, 'fichasaude') else ""

    @property
    def intolerancia_alimentar(self):
        return self.fichasaude.restricao_alimentar if hasattr(self, 'fichasaude') else ""

    @property
    def doenca_cronica(self):
        return self.fichasaude.doenca_cronica if hasattr(self, 'fichasaude') else ""

    @property
    def uso_medicamento_controlado(self):
        return self.fichasaude.medicamento_continuo if hasattr(self, 'fichasaude') else ""

    @property
    def observacoes_pais(self):
        return self.fichasaude.contato_emergencia if hasattr(self, 'fichasaude') else ""

    @property
    def tamanho_camisa(self):
        camisa = self.camisas_recebidas.order_by('-ano').first()
        return camisa.tamanho_camisa if camisa else ""

    @property
    def total_presencas(self):
        return self.frequencias.filter(evento__categoria__nome="Missa").count()

    @property
    def progresso_percentual(self):
        return min((self.total_presencas / 52) * 100, 100)

    @property
    def status_aptidao(self):
        from datetime import date
        hoje = date.today()
        inicio = date(hoje.year, 9, 1)
        if hoje < inicio:
            inicio = date(hoje.year - 1, 9, 1)
        semanas = (hoje - inicio).days // 7
        if self.total_presencas >= 52:
            return "Apto"
        elif self.total_presencas >= semanas:
            return "Frequência constante"
        return "Frequência baixa"

    def progresso_por_cirio(self, cirio):
        progresso = []
        for regra in cirio.regras.all():
            total = self.frequencias.filter(
                evento__categoria=regra.categoria,
                evento__data__range=(cirio.inicio, cirio.termino)
            ).count()
            progresso.append({
                "categoria": regra.categoria.nome,
                "feito": total,
                "necessario": regra.quantidade_necessaria,
                "ok": total >= regra.quantidade_necessaria
            })
        return progresso

class ResponsavelGuarda(models.Model):
    guarda = models.ForeignKey(Guarda, on_delete=models.CASCADE, related_name="responsaveis")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE)
    parentesco = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "RESPONSAVEL_GUARDA"
        unique_together = (('guarda', 'pessoa'),)

class PadrinhoGuarda(models.Model):
    guarda = models.ForeignKey(Guarda, on_delete=models.CASCADE, related_name="padrinhos")
    padrinho = models.ForeignKey(Guarda, on_delete=models.CASCADE, related_name="afilhados")

    class Meta:
        db_table = "PADRINHO_GUARDA"
        unique_together = (('guarda', 'padrinho'),)

class GuardaApoio(models.Model):
    matricula = models.CharField(max_length=7)
    responsavel = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    paroquia = models.CharField(max_length=255)
    telefone = models.CharField(max_length=50)
