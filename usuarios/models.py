from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Tipo(models.TextChoices):
        COORDENADOR = 'COORD', 'Coordenador'
        MEMBRO = 'MEMBRO', 'Membro'

    matricula = models.CharField('Matrícula', max_length=20, unique=True)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.MEMBRO)
    criado_por = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='criados'
    )

    @property
    def is_coordenador(self):
        return self.tipo == self.Tipo.COORDENADOR

    def __str__(self):
        return self.get_full_name() or self.username


class RegistroPresenca(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='registros_presenca')
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora']

    def __str__(self):
        return f'{self.usuario} - ENTRADA ({self.data_hora:%d/%m %H:%M})'
