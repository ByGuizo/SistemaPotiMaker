from django.conf import settings
from django.db import models


class Projeto(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def em_andamento(self):
        return self.atividades.exclude(status=Atividade.Status.CONCLUIDO).exists()


class Atividade(models.Model):
    class Status(models.TextChoices):
        A_FAZER = 'A_FAZER', 'A Fazer'
        FAZENDO = 'FAZENDO', 'Fazendo'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'

    class Prioridade(models.TextChoices):
        BAIXA = 'BAIXA', 'Baixa'
        MEDIA = 'MEDIA', 'Média'
        ALTA = 'ALTA', 'Alta'

    ORDEM_STATUS = [Status.A_FAZER, Status.FAZENDO, Status.CONCLUIDO]

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='atividades')
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    documento_tecnico = models.FileField(upload_to='projetos/docs/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.A_FAZER)
    prioridade = models.CharField(max_length=6, choices=Prioridade.choices, default=Prioridade.MEDIA)
    prazo = models.DateField(null=True, blank=True)
    membros = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='atividades', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-prioridade', 'prazo']

    def __str__(self):
        return f'{self.projeto.nome} — {self.nome}'

    def mover(self, direcao):
        idx = self.ORDEM_STATUS.index(self.status)
        novo_idx = idx + (1 if direcao == 'frente' else -1)
        if 0 <= novo_idx < len(self.ORDEM_STATUS):
            self.status = self.ORDEM_STATUS[novo_idx]
            self.save(update_fields=['status'])
