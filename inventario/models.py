from django.db import models


class Item(models.Model):
    class Categoria(models.TextChoices):
        ELETRONICO = 'ELETRONICO', 'Eletrônico'
        FERRAMENTA = 'FERRAMENTA', 'Ferramenta'
        CONSUMIVEL = 'CONSUMIVEL', 'Consumível'
        EQUIPAMENTO = 'EQUIPAMENTO', 'Equipamento'

    class Status(models.TextChoices):
        DISPONIVEL = 'DISPONIVEL', 'Disponível'
        EM_USO = 'EM_USO', 'Em uso'
        MANUTENCAO = 'MANUTENCAO', 'Manutenção'

    nome = models.CharField(max_length=120)
    categoria = models.CharField(max_length=15, choices=Categoria.choices)
    quantidade = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DISPONIVEL)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome
