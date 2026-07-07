from django.utils import timezone

from .models import RegistroPresenca


def status_laboratorio():
    hoje = timezone.localdate()
    entradas_hoje = RegistroPresenca.objects.filter(data_hora__date=hoje)
    return {
        'aberto': entradas_hoje.exists(),
        'qtd_presentes': entradas_hoje.values('usuario').distinct().count(),
    }
