from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from agenda.services import proximo_evento

from .decorators import coordenador_required
from .forms import LoginForm, MembroForm
from .models import RegistroPresenca
from .services import status_laboratorio

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


@login_required
def registrar_presenca(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        usuario = get_object_or_404(Usuario, pk=usuario_id)
        RegistroPresenca.objects.create(usuario=usuario)

    contexto = {
        'membros': Usuario.objects.filter(is_active=True).order_by('first_name'),
        'registros': RegistroPresenca.objects.select_related('usuario')[:10],
        'status_lab': status_laboratorio(),
        'proximo_evento': proximo_evento(),
    }
    return render(request, 'core/partials/_presenca.html', contexto)
