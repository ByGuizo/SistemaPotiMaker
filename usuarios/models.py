from datetime import time

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    class Tipo(models.TextChoices):
        COORDENADOR = 'COORD', 'Coordenador'
        MEMBRO = 'MEMBRO', 'Membro'

    class StatusCadastro(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        APROVADO = 'APROVADO', 'Aprovado'

    matricula = models.CharField('Matrícula', max_length=20, unique=True)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.MEMBRO)
    status_cadastro = models.CharField(
        'Status do cadastro', max_length=10,
        choices=StatusCadastro.choices, default=StatusCadastro.APROVADO
    )
    criado_por = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='criados'
    )
    aprovado_por = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='aprovados'
    )
    aprovado_em = models.DateTimeField(null=True, blank=True)

    @property
    def is_coordenador(self):
        return self.tipo == self.Tipo.COORDENADOR

    @property
    def is_pendente(self):
        return self.status_cadastro == self.StatusCadastro.PENDENTE

    def aprovar(self, coordenador):
        self.status_cadastro = self.StatusCadastro.APROVADO
        self.is_active = True
        self.aprovado_por = coordenador
        self.aprovado_em = timezone.now()
        self.save(update_fields=['status_cadastro', 'is_active', 'aprovado_por', 'aprovado_em'])

    def __str__(self):
        return self.get_full_name() or self.username


class RegistroPresenca(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='registros_presenca')
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora']

    def __str__(self):
        return f'{self.usuario} - ENTRADA ({self.data_hora:%d/%m %H:%M})'


class HorarioEscala(models.Model):
    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 0, 'Segunda'
        TERCA = 1, 'Terça'
        QUARTA = 2, 'Quarta'
        QUINTA = 3, 'Quinta'
        SEXTA = 4, 'Sexta'

    class Slot(models.TextChoices):
        M1 = 'M1', '07:00 – 08:30'
        M2 = 'M2', '08:50 – 10:20'
        M3 = 'M3', '10:30 – 12:00'
        T1 = 'T1', '13:00 – 14:30'
        T2 = 'T2', '14:50 – 16:20'
        T3 = 'T3', '16:30 – 18:00'

    HORARIOS = {
        Slot.M1: (time(7, 0), time(8, 30)),
        Slot.M2: (time(8, 50), time(10, 20)),
        Slot.M3: (time(10, 30), time(12, 0)),
        Slot.T1: (time(13, 0), time(14, 30)),
        Slot.T2: (time(14, 50), time(16, 20)),
        Slot.T3: (time(16, 30), time(18, 0)),
    }

    dia_semana = models.IntegerField(choices=DiaSemana.choices)
    slot = models.CharField(max_length=2, choices=Slot.choices)
    membros = models.ManyToManyField(Usuario, related_name='horarios_escala', blank=True)

    class Meta:
        ordering = ['dia_semana', 'slot']
        unique_together = ['dia_semana', 'slot']

    def __str__(self):
        return f'{self.get_dia_semana_display()} {self.get_slot_display()}'

    @property
    def hora_inicio(self):
        return self.HORARIOS[self.slot][0]

    @property
    def hora_fim(self):
        return self.HORARIOS[self.slot][1]
