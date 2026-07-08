from django.shortcuts import render

from agenda.services import eventos_da_semana, proximo_evento
from inventario.models import Item
from projetos.models import Projeto
from usuarios.models import Usuario
from usuarios.services import escala_atual, status_laboratorio


def dashboard(request):
    contexto = {
        'qtd_membros_ativos': Usuario.objects.filter(is_active=True).count(),
        'qtd_projetos_andamento': Projeto.objects.exclude(status=Projeto.Status.CONCLUIDO).count(),
        'qtd_itens_inventario': Item.objects.count(),
        'qtd_eventos_semana': eventos_da_semana().count(),
        'escala': escala_atual(),
        'status_lab': status_laboratorio(),
        'proximo_evento': proximo_evento(),
    }
    return render(request, 'core/dashboard.html', contexto)
