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
    """
    Quem deve estar no laboratório agora.

    Retorna um dict com o `horario` e um flag `em_andamento`:
    - `em_andamento=True`  → a hora atual está dentro do slot.
    - `em_andamento=False` → estamos num intervalo (entre slots, antes do
      primeiro ou depois do último) e o `horario` é o **próximo** do dia.

    Os slots não cobrem o dia inteiro (há 2h de intervalos entre eles, mais o
    almoço), então olhar só "dentro do slot" deixava o painel vazio em ~14% do
    expediente mesmo com a escala preenchida. Fora de dia útil retorna None.
    """
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
    # Ordena pelo horário real do slot, não pela string ('M1' < 'T1' por acaso)
    horarios.sort(key=lambda h: h.hora_inicio)

    for horario in horarios:
        if horario.hora_inicio <= hora <= horario.hora_fim:
            return {'horario': horario, 'em_andamento': True}

    # Fora de qualquer slot: aponta o próximo do dia, se ainda houver
    for horario in horarios:
        if hora < horario.hora_inicio:
            return {'horario': horario, 'em_andamento': False}

    # Expediente do dia encerrado
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
