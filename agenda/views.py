import calendar

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from usuarios.decorators import coordenador_required

from .forms import EventoForm
from .models import Evento
from .utils import DIAS_SEMANA_PT, MESES_PT


def _grade_mes(ano, mes):
    cal = calendar.Calendar(firstweekday=0)
    hoje = timezone.localdate()

    eventos_por_dia = {}
    for evento in Evento.objects.filter(data__year=ano, data__month=mes):
        eventos_por_dia.setdefault(evento.data.day, []).append(evento)

    semanas = []
    semana = []
    for dia in cal.itermonthdates(ano, mes):
        semana.append({
            'data': dia,
            'no_mes': dia.month == mes,
            'hoje': dia == hoje,
            'eventos': eventos_por_dia.get(dia.day, []) if dia.month == mes else [],
        })
        if len(semana) == 7:
            semanas.append(semana)
            semana = []
    return semanas


def calendario(request):
    hoje = timezone.localdate()
    ano = int(request.GET.get('ano', hoje.year))
    mes = int(request.GET.get('mes', hoje.month))

    if mes < 1:
        mes, ano = 12, ano - 1
    elif mes > 12:
        mes, ano = 1, ano + 1

    contexto = {
        'semanas': _grade_mes(ano, mes),
        'ano': ano,
        'mes': mes,
        'nome_mes': MESES_PT[mes],
        'dias_semana': DIAS_SEMANA_PT,
        'mes_anterior': mes - 1,
        'ano_anterior': ano if mes > 1 else ano - 1,
        'mes_seguinte': mes + 1,
        'ano_seguinte': ano if mes < 12 else ano + 1,
    }
    template = 'agenda/partials/_grade_mes.html' if request.headers.get('HX-Request') else 'agenda/calendario.html'
    return render(request, template, contexto)


def painel_dia(request, ano, mes, dia):
    data = timezone.datetime(ano, mes, dia).date()
    eventos = Evento.objects.filter(data=data)
    contexto = {'data': data, 'eventos': eventos}
    return render(request, 'agenda/partials/_painel_dia.html', contexto)


@login_required
def novo_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.criado_por = request.user
            evento.save()
            return redirect('agenda:calendario')
    else:
        data_inicial = request.GET.get('data', '')
        form = EventoForm(initial={'data': data_inicial})
    contexto = {'form': form, 'titulo': 'Novo Evento', 'voltar_url': reverse_lazy('agenda:calendario')}
    return render(request, 'agenda/evento_form.html', contexto)


@login_required
def editar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return redirect('agenda:calendario')
    else:
        form = EventoForm(instance=evento)
    contexto = {'form': form, 'titulo': 'Editar Evento', 'voltar_url': reverse_lazy('agenda:calendario')}
    return render(request, 'agenda/evento_form.html', contexto)


@coordenador_required
def excluir_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        evento.delete()
    return redirect('agenda:calendario')
