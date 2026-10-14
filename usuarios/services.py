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

    horarios = list(
        HorarioEscala.objects
        .filter(dia_semana=dia_semana)
        .prefetch_related('membros')
    )
    horarios.sort(key=lambda h: h.hora_inicio)

    for horario in horarios:
        if horario.hora_inicio <= hora <= horario.hora_fim:
            return {'horario': horario, 'em_andamento': True}

    for horario in horarios:
        if hora < horario.hora_inicio:
            return {'horario': horario, 'em_andamento': False}

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


def grade_por_dia():
    horarios = HorarioEscala.objects.prefetch_related('membros').all()
    mapa = {(h.dia_semana, h.slot): h for h in horarios}

    dias = []
    for dia_valor, dia_label in HorarioEscala.DiaSemana.choices:
        slots = [
            {'slot': slot_valor, 'label': slot_label,
             'horario': mapa.get((dia_valor, slot_valor))}
            for slot_valor, slot_label in HorarioEscala.Slot.choices
        ]
        dias.append({'valor': dia_valor, 'label': dia_label, 'slots': slots})
    return dias
