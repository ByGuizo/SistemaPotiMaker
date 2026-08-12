from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from projetos.models import Projeto

from .decorators import coordenador_required
from .forms import CadastroForm, LoginForm, MembroForm
from .models import HorarioEscala
from .services import grade_horarios

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

    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Cadastro enviado! Aguarde a aprovação de um coordenador para acessar o sistema.'
            )
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
    membro = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = MembroForm(request.POST, instance=membro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Membro atualizado com sucesso.')
            return redirect('usuarios:lista_membros')
    else:
        form = MembroForm(instance=membro)
    contexto = {'form': form, 'titulo': 'Editar Membro', 'voltar_url': reverse_lazy('usuarios:lista_membros')}
    return render(request, 'usuarios/membro_form.html', contexto)


@coordenador_required
def excluir_membro(request, pk):
    membro = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        membro.delete()
        messages.success(request, 'Membro excluído.')
    return redirect('usuarios:lista_membros')


@login_required
def perfil(request):
    contexto = {
        'membro': request.user,
        'projetos': Projeto.objects.filter(atividades__membros=request.user).distinct(),
        'registros': request.user.registros_presenca.all()[:10],
    }
    return render(request, 'usuarios/perfil.html', contexto)


@coordenador_required
def editar_horarios(request):
    if request.method == 'POST':
        for dia_valor, _dia_label in HorarioEscala.DiaSemana.choices:
            for slot_valor, _slot_label in HorarioEscala.Slot.choices:
                nome_campo = f'celula_{dia_valor}_{slot_valor}'
                ids_membros = request.POST.getlist(nome_campo)
                horario, _criado = HorarioEscala.objects.get_or_create(dia_semana=dia_valor, slot=slot_valor)
                horario.membros.set(ids_membros)
        messages.success(request, 'Escala de horários atualizada com sucesso.')
        return redirect('core:dashboard')

    contexto = {
        'linhas': grade_horarios(),
        'dias': HorarioEscala.DiaSemana.choices,
        'membros': Usuario.objects.filter(is_active=True).order_by('first_name'),
    }
    return render(request, 'usuarios/editar_horarios.html', contexto)
