from django.db import models


class FichaSaude(models.Model):
    pessoa = models.OneToOneField(
        "pessoa.Pessoa", on_delete=models.CASCADE, related_name="ficha_saude"
    )

    # Condições / diagnósticos
    autismo = models.BooleanField(default=False)
    tdah = models.BooleanField(default=False)
    alzheimer = models.BooleanField(default=False)
    demencia = models.BooleanField(default=False)
    parkinson = models.BooleanField(default=False)
    diabetes = models.BooleanField(default=False)
    hipertensao = models.BooleanField(default=False)
    problema_cardiaco = models.BooleanField(default=False)
    problema_renal = models.BooleanField(default=False)
    osteoporose = models.BooleanField(default=False)
    artrite = models.BooleanField(default=False)

    # Mobilidade / dispositivos
    usa_cadeira_rodas = models.BooleanField(default=False)
    usa_andador = models.BooleanField(default=False)
    usa_bengala = models.BooleanField(default=False)
    deficiencia_visual = models.BooleanField(default=False)
    deficiencia_auditiva = models.BooleanField(default=False)
    usa_protese = models.BooleanField(default=False)

    # Saúde mental
    depressao = models.BooleanField(default=False)
    ansiedade = models.BooleanField(default=False)

    # Informações textuais
    alergia = models.CharField(max_length=250, null=True, blank=True)
    intolerancia_alimentar = models.CharField(max_length=250, null=True, blank=True)
    doenca_cronica = models.CharField(max_length=250, null=True, blank=True)
    uso_medicamento_controlado = models.CharField(max_length=250, null=True, blank=True)
    plano_saude = models.CharField(max_length=250, null=True, blank=True)
    tipo_sanguineo = models.CharField(max_length=150, null=True, blank=True)

    contato_emergencia_nome = models.CharField(max_length=200, null=True, blank=True)
    contato_emergencia_telefone = models.CharField(max_length=50, null=True, blank=True)

    observacao = models.CharField(max_length=250, null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "FICHA_SAUDE"

    def __str__(self):
        return f"Ficha de saúde - {self.pessoa.nome}"
