"""
Proteções contra força bruta: bloqueio de login (django-axes) e limite de
cadastros por IP. As funções de axes são ligadas no settings pelos nomes
AXES_CLIENT_IP_CALLABLE, AXES_USERNAME_CALLABLE e AXES_LOCKOUT_CALLABLE.
"""
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render

LIMITE_CADASTROS_POR_HORA = 5
JANELA_CADASTRO_SEGUNDOS = 60 * 60


def ip_do_cliente(request):
    """
    IP de quem fez a requisição.

    Atrás do nginx, REMOTE_ADDR é sempre o do próprio nginx (127.0.0.1) — todo
    mundo pareceria o mesmo usuário. O nginx informa o IP real no cabeçalho
    X-Real-IP, mas esse cabeçalho só é confiável se o gunicorn NÃO estiver
    exposto direto (senão qualquer um inventa um IP). Por isso só é lido com
    DJANGO_CONFIAR_X_REAL_IP=True, ligado junto com a configuração do nginx.
    """
    if settings.CONFIAR_X_REAL_IP:
        ip = request.META.get('HTTP_X_REAL_IP', '').strip()
        if ip:
            return ip
    return request.META.get('REMOTE_ADDR')


def usuario_para_axes(request, credentials):
    """
    Nome de usuário usado na contagem de tentativas, sem diferenciar maiúsculas:
    'Guizo', 'guizo' e 'GUIZO' somam no mesmo contador. Sem isso, cada variação
    ganharia 5 tentativas próprias.
    """
    username = (credentials or {}).get('username') or request.POST.get('username', '')
    return username.strip().lower()


def minutos_de_bloqueio():
    return int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)


def resposta_bloqueio(request, original_response=None, credentials=None):
    """Tela de login com a mensagem de bloqueio em português (HTTP 429)."""
    from .forms import LoginForm

    form = LoginForm(request, initial={'username': request.POST.get('username', '')})
    contexto = {
        'form': form,
        'mensagem_bloqueio': (
            'Muitas tentativas de login sem sucesso. Por segurança, o acesso foi '
            f'bloqueado por {minutos_de_bloqueio()} minutos. Tente novamente mais tarde.'
        ),
    }
    return render(request, 'usuarios/login.html', contexto, status=429)


def _chave_cadastro(request):
    return f'cadastros-por-ip:{ip_do_cliente(request)}'


def cadastro_bloqueado(request):
    """True se este IP já fez o máximo de cadastros permitido na última hora."""
    return cache.get(_chave_cadastro(request), 0) >= LIMITE_CADASTROS_POR_HORA


def registrar_cadastro(request):
    """Soma um cadastro para o IP. A janela de 1 hora conta a partir do primeiro."""
    chave = _chave_cadastro(request)
    if not cache.add(chave, 1, timeout=JANELA_CADASTRO_SEGUNDOS):
        try:
            cache.incr(chave)
        except ValueError:
            # A chave expirou entre o add() e o incr(): começa uma janela nova
            cache.add(chave, 1, timeout=JANELA_CADASTRO_SEGUNDOS)
