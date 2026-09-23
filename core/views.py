from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.utils import timezone

from agenda.models import Evento
from agenda.services import eventos_da_semana
from inventario.models import Item
from projetos.models import Atividade, Projeto
from usuarios.models import Usuario
from usuarios.services import escala_atual

STATUS_ABERTOS = [Atividade.Status.A_FAZER, Atividade.Status.FAZENDO]


def dashboard(request):
    hoje = timezone.localdate()

    qtd_projetos_andamento = Projeto.objects.filter(
        atividades__status__in=STATUS_ABERTOS
    ).distinct().count()

    atividades_abertas = Atividade.objects.filter(status__in=STATUS_ABERTOS)

    minhas_atividades = atividades_abertas.filter(
        membros=request.user
    ).select_related('projeto')[:5] if request.user.is_authenticated else []

    cadastros_pendentes = Usuario.objects.filter(
        status_cadastro=Usuario.StatusCadastro.PENDENTE
    ).order_by('date_joined') if request.user.is_authenticated and request.user.is_coordenador else None

    contexto = {
        'cadastros_pendentes': cadastros_pendentes,
        'qtd_membros_ativos': Usuario.objects.filter(is_active=True).count(),
        'qtd_projetos_andamento': qtd_projetos_andamento,
        'qtd_itens_inventario': Item.objects.count(),
        'qtd_eventos_semana': eventos_da_semana().count(),
        'escala': escala_atual(),
        'minhas_atividades': minhas_atividades,
        'atividades_atrasadas': atividades_abertas.filter(
            prazo__lt=hoje
        ).select_related('projeto')[:5],
        'proximos_eventos': Evento.objects.filter(data__gte=hoje)[:4],
        'itens_manutencao': Item.objects.filter(status=Item.Status.MANUTENCAO)[:5],
    }
    return render(request, 'core/dashboard.html', contexto)


# Fotos de perfil abrem no navegador; todo o resto (documentos técnicos) é baixado
PASTAS_INLINE = ('perfis/',)
EXTENSOES_INLINE = {'.jpg', '.jpeg', '.png', '.webp'}


@login_required
def servir_media(request, caminho):
    """
    Entrega os arquivos enviados (media/) só para quem está logado.

    Substitui o static() do Django, que só funciona com DEBUG=True e não exige
    login. O caminho vem da URL, então é resolvido e conferido: tem que continuar
    dentro de MEDIA_ROOT — "../settings.py" ou "C:/Windows/..." viram 404.
    """
    raiz = Path(settings.MEDIA_ROOT).resolve()
    try:
        arquivo = (raiz / caminho).resolve()
    except (OSError, ValueError):
        raise Http404
    if not arquivo.is_relative_to(raiz) or not arquivo.is_file():
        raise Http404

    relativo = arquivo.relative_to(raiz).as_posix()
    inline = relativo.startswith(PASTAS_INLINE) and arquivo.suffix.lower() in EXTENSOES_INLINE
    resposta = FileResponse(open(arquivo, 'rb'), as_attachment=not inline, filename=arquivo.name)
    # Mesmo que um arquivo perigoso passe, o navegador não executa scripts dele
    resposta['Content-Security-Policy'] = "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox"
    return resposta
