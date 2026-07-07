from django.shortcuts import render

from agenda.services import eventos_da_semana, proximo_evento
from inventario.models import Item
from projetos.models import Projeto
from usuarios.models import RegistroPresenca, Usuario
from usuarios.services import status_laboratorio


def dashboard(request):
    contexto = {
        'qtd_membros_ativos': Usuario.objects.filter(is_active=True).count(),
        'qtd_projetos_andamento': Projeto.objects.exclude(status=Projeto.Status.CONCLUIDO).count(),
        'qtd_itens_inventario': Item.objects.count(),
        'qtd_eventos_semana': eventos_da_semana().count(),
        'membros': Usuario.objects.filter(is_active=True).order_by('first_name'),
        'registros': RegistroPresenca.objects.select_related('usuario')[:10],
        'status_lab': status_laboratorio(),
        'proximo_evento': proximo_evento(),
    }
    return render(request, 'core/dashboard.html', contexto)
