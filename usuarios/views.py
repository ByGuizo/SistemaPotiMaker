from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from projetos.models import Projeto

from .decorators import coordenador_required
from .forms import CadastroForm, LoginForm, MembroForm, PerfilForm
from .models import HorarioEscala
from .seguranca import cadastro_bloqueado, registrar_cadastro
from .services import grade_horarios, grade_por_dia

Usuario = get_user_model()


class PotiMakerLoginView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm


class PotiMakerLogoutView(LogoutView):
    pass


def cadastro(request):
    """Auto-cadastro público — cria o usuário pendente de aprovação do coordenador."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    mensagem_sucesso = 'Cadastro enviado! Aguarde a aprovação de um coordenador para acessar o sistema.'
    if request.method == 'POST':
        if request.POST.get(CadastroForm.CAMPO_ARMADILHA):
            # Robô: responde como se tivesse dado certo, para ele não perceber, e não cria nada
            messages.success(request, mensagem_sucesso)
            return redirect('usuarios:login')

        form = CadastroForm(request.POST)
        if cadastro_bloqueado(request):
            form.is_valid()
            form.add_error(None, (
                'Foram feitos muitos cadastros a partir desta rede na última hora. '
                'Tente novamente mais tarde.'
            ))
            return render(request, 'usuarios/cadastro.html', {'form': form}, status=429)

        if form.is_valid():
            form.save()
            registrar_cadastro(request)
            messages.success(request, mensagem_sucesso)
            return redirect('usuarios:login')
    else:
        form = CadastroForm()
    return render(request, 'usuarios/cadastro.html', {'form': form})


def lista_membros(request):
    termo = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    membros = Usuario.objects.filter(
        status_cadastro=Usuario.StatusCadastro.APROVADO
    ).order_by('first_name', 'username')
    if termo:
        membros = membros.filter(
            Q(first_name__icontains=termo) | Q(username__icontains=termo) | Q(matricula__icontains=termo)
        )
    if tipo:
        membros = membros.filter(tipo=tipo)

    contexto = {'membros': membros, 'termo': termo, 'tipo': tipo}
    template = 'usuarios/partials/_lista_membros.html' if request.headers.get('HX-Request') else 'usuarios/membros.html'
    return render(request, template, contexto)


def _destino_seguro(request):
    """Só aceita redirecionamento para uma URL interna (evita open redirect)."""
    proximo = request.POST.get('proximo')
    if proximo and url_has_allowed_host_and_scheme(
        proximo, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return proximo
    return reverse_lazy('core:dashboard')


@coordenador_required
def aprovar_cadastro(request, pk):
    pendente = get_object_or_404(Usuario, pk=pk, status_cadastro=Usuario.StatusCadastro.PENDENTE)
    if request.method == 'POST':
        pendente.aprovar(request.user)
        messages.success(request, f'Cadastro de {pendente} aprovado.')
    return redirect(_destino_seguro(request))


@coordenador_required
def negar_cadastro(request, pk):
    pendente = get_object_or_404(Usuario, pk=pk, status_cadastro=Usuario.StatusCadastro.PENDENTE)
    if request.method == 'POST':
        nome = str(pendente)
        pendente.delete()
        messages.success(request, f'Cadastro de {nome} negado e removido.')
    return redirect(_destino_seguro(request))


@coordenador_required
def editar_membro(request, pk):
    # Pendente não é editado aqui: o único caminho é aprovar (Usuario.aprovar) ou negar.
    # Sem o filtro, marcar "Ativo" nesta tela liberava o login sem aprovação.
    membro = get_object_or_404(Usuario, pk=pk, status_cadastro=Usuario.StatusCadastro.APROVADO)
    if request.method == 'POST':
        form = MembroForm(request.POST, instance=membro, editor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Membro atualizado com sucesso.')
            return redirect('usuarios:lista_membros')
    else:
        form = MembroForm(instance=membro, editor=request.user)
    contexto = {'form': form, 'titulo': 'Editar Membro', 'voltar_url': reverse_lazy('usuarios:lista_membros')}
    return render(request, 'usuarios/membro_form.html', contexto)


@coordenador_required
def excluir_membro(request, pk):
    membro = get_object_or_404(Usuario, pk=pk, status_cadastro=Usuario.StatusCadastro.APROVADO)
    if request.method == 'POST':
        if membro.pk == request.user.pk:
            messages.error(request, 'Você não pode excluir a sua própria conta.')
        elif membro.e_ultimo_coordenador_ativo():
            messages.error(
                request,
                'Não é possível excluir o último coordenador ativo. Promova outro membro a coordenador antes.'
            )
        else:
            membro.delete()
            messages.success(request, 'Membro excluído.')
    return redirect('usuarios:lista_membros')


def _contexto_perfil(membro, request):
    return {
        'membro': membro,
        'projetos': Projeto.objects.filter(atividades__membros=membro).distinct(),
        'registros': membro.registros_presenca.all()[:10],
        # Controla os botões de editar/reportar sem repetir a comparação no template
        'proprio_perfil': membro.pk == request.user.pk,
    }


@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html', _contexto_perfil(request.user, request))


@login_required
def perfil_membro(request, pk):
    """Perfil público de outro membro. Pendentes não são visíveis."""
    membro = get_object_or_404(
        Usuario, pk=pk, status_cadastro=Usuario.StatusCadastro.APROVADO
    )
    if membro.pk == request.user.pk:
        return redirect('usuarios:perfil')
    return render(request, 'usuarios/perfil.html', _contexto_perfil(membro, request))


@login_required
def editar_perfil(request):
    """Cada membro edita o próprio perfil — sem pk, sempre request.user."""
    usuario = Usuario.objects.get(pk=request.user.pk)
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('usuarios:perfil')
    else:
        form = PerfilForm(instance=usuario)
    contexto = {'form': form, 'titulo': 'Editar Perfil', 'voltar_url': reverse_lazy('usuarios:perfil')}
    return render(request, 'usuarios/perfil_form.html', contexto)


def _membros_escalaveis():
    """Quem pode entrar na escala: membros aprovados e ativos."""
    return Usuario.objects.filter(is_active=True, status_cadastro=Usuario.StatusCadastro.APROVADO)


def _ids_permitidos(valores, permitidos):
    """
    Converte os valores enviados em IDs, descartando o que não serve.

    O POST pode ser montado à mão: "abc" ou um número gigante estourariam
    ValueError no membros.set() e um ID inexistente violaria a chave
    estrangeira (erro 500 nos dois casos); um ID de pendente entraria na
    escala. Aqui só passa inteiro que esteja em `permitidos`.
    """
    ids = set()
    for valor in valores:
        try:
            pk = int(valor)
        except (TypeError, ValueError):
            continue
        if pk in permitidos:
            ids.add(pk)
    return ids


@coordenador_required
def editar_horarios(request):
    if request.method == 'POST':
        permitidos = set(_membros_escalaveis().values_list('pk', flat=True))
        # Tudo ou nada: se uma célula falhar no meio, as anteriores não ficam
        # gravadas pela metade — a escala continua como estava.
        with transaction.atomic():
            for dia_valor, _dia_label in HorarioEscala.DiaSemana.choices:
                for slot_valor, _slot_label in HorarioEscala.Slot.choices:
                    nome_campo = f'celula_{dia_valor}_{slot_valor}'
                    ids_membros = _ids_permitidos(request.POST.getlist(nome_campo), permitidos)
                    horario, _criado = HorarioEscala.objects.get_or_create(dia_semana=dia_valor, slot=slot_valor)
                    horario.membros.set(ids_membros)
        messages.success(request, 'Escala de horários atualizada com sucesso.')
        return redirect('core:dashboard')

    contexto = {
        'linhas': grade_horarios(),
        'grade_dias': grade_por_dia(),
        'dias': HorarioEscala.DiaSemana.choices,
        'membros': _membros_escalaveis().order_by('first_name'),
    }
    return render(request, 'usuarios/editar_horarios.html', contexto)
