from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .decorators import coordenador_required
from .forms import LoginForm, MembroForm
from .models import HorarioEscala
from .services import grade_horarios

Usuario = get_user_model()


class PotiMakerLoginView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm


class PotiMakerLogoutView(LogoutView):
    pass


def lista_membros(request):
    termo = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    membros = Usuario.objects.all().order_by('first_name', 'username')
    if termo:
        membros = membros.filter(
            Q(first_name__icontains=termo) | Q(last_name__icontains=termo) | Q(email__icontains=termo)
        )
    if tipo:
        membros = membros.filter(tipo=tipo)

    contexto = {'membros': membros, 'termo': termo, 'tipo': tipo}
    template = 'usuarios/partials/_lista_membros.html' if request.headers.get('HX-Request') else 'usuarios/membros.html'
    return render(request, template, contexto)


@coordenador_required
def novo_membro(request):
    if request.method == 'POST':
        form = MembroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Membro criado com sucesso.')
            return redirect('usuarios:lista_membros')
    else:
        form = MembroForm()
    contexto = {'form': form, 'titulo': 'Novo Membro', 'voltar_url': reverse_lazy('usuarios:lista_membros')}
    return render(request, 'usuarios/membro_form.html', contexto)


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
        'projetos': request.user.projetos.all(),
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
