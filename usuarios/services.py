from django.utils import timezone

from .models import HorarioEscala, RegistroPresenca


def status_laboratorio():
    hoje = timezone.localdate()
    entradas_hoje = RegistroPresenca.objects.filter(data_hora__date=hoje)
    return {
        'aberto': entradas_hoje.exists(),
        'qtd_presentes': entradas_hoje.values('usuario').distinct().count(),
    }


def escala_atual():
    agora = timezone.localtime()
    dia_semana = agora.weekday()
    hora = agora.time()

    if dia_semana > 4:
        return None

    for horario in HorarioEscala.objects.filter(dia_semana=dia_semana).prefetch_related('membros'):
        if horario.hora_inicio <= hora <= horario.hora_fim:
            return horario
    return None


def grade_horarios():
    horarios = HorarioEscala.objects.prefetch_related('membros').all()
    mapa = {(h.dia_semana, h.slot): h for h in horarios}

    linhas = []
    for slot_valor, slot_label in HorarioEscala.Slot.choices:
        linha = {'slot': slot_valor, 'label': slot_label, 'dias': []}
        for dia_valor, _dia_label in HorarioEscala.DiaSemana.choices:
            linha['dias'].append(mapa.get((dia_valor, slot_valor)))
        linhas.append(linha)
    return linhas
