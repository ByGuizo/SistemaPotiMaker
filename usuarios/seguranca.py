from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render

LIMITE_CADASTROS_POR_HORA = 5
JANELA_CADASTRO_SEGUNDOS = 60 * 60


def ip_do_cliente(request):
    if settings.CONFIAR_X_REAL_IP:
        ip = request.META.get('HTTP_X_REAL_IP', '').strip()
        if ip:
            return ip
    return request.META.get('REMOTE_ADDR')


def usuario_para_axes(request, credentials):
    username = (credentials or {}).get('username') or request.POST.get('username', '')
    return username.strip().lower()


def minutos_de_bloqueio():
    return int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)


def resposta_bloqueio(request, original_response=None, credentials=None):
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
    return cache.get(_chave_cadastro(request), 0) >= LIMITE_CADASTROS_POR_HORA


def registrar_cadastro(request):
    chave = _chave_cadastro(request)
    if not cache.add(chave, 1, timeout=JANELA_CADASTRO_SEGUNDOS):
        try:
            cache.incr(chave)
        except ValueError:
            cache.add(chave, 1, timeout=JANELA_CADASTRO_SEGUNDOS)
