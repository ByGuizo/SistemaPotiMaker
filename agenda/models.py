from django.conf import settings
from django.db import models


class Evento(models.Model):
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    data = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fim = models.TimeField(null=True, blank=True)
    local = models.CharField(max_length=120, blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_criados'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data', 'hora_inicio']

    def __str__(self):
        return f'{self.titulo} ({self.data:%d/%m/%Y})'
