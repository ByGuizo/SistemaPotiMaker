from datetime import timedelta

from django.utils import timezone

from .models import Evento


def proximo_evento():
    hoje = timezone.localdate()
    return Evento.objects.filter(data__gte=hoje).order_by('data', 'hora_inicio').first()


def eventos_da_semana():
    hoje = timezone.localdate()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    return Evento.objects.filter(data__range=[inicio_semana, fim_semana])
