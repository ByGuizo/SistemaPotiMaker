from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from usuarios.decorators import coordenador_required

from .forms import AtividadeForm, ProjetoForm
from .models import Atividade, Projeto


def kanban(request):
    projeto_id = request.GET.get('projeto', '')

    colunas = []
    for status_valor, status_label in Atividade.Status.choices:
        atividades = Atividade.objects.filter(status=status_valor).select_related('projeto').prefetch_related('membros')
        if projeto_id:
            atividades = atividades.filter(projeto_id=projeto_id)
        colunas.append({'valor': status_valor, 'label': status_label, 'atividades': atividades})

    contexto = {
        'colunas': colunas,
        'projetos': Projeto.objects.all(),
        'projeto_id': projeto_id,
    }
    template = 'projetos/partials/_kanban_colunas.html' if request.headers.get('HX-Request') else 'projetos/kanban.html'
    return render(request, template, contexto)


@login_required
def mover_atividade(request, pk, direcao):
    if request.method == 'POST':
        atividade = get_object_or_404(Atividade, pk=pk)
        atividade.mover(direcao)
    return kanban(request)


@login_required
def nova_atividade(request):
    if request.method == 'POST':
        form = AtividadeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('projetos:kanban')
    else:
        form = AtividadeForm(initial={'projeto': request.GET.get('projeto')})
    contexto = {'form': form, 'titulo': 'Nova Atividade', 'voltar_url': reverse_lazy('projetos:kanban')}
    return render(request, 'projetos/atividade_form.html', contexto)


@login_required
def editar_atividade(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    if request.method == 'POST':
        form = AtividadeForm(request.POST, request.FILES, instance=atividade)
        if form.is_valid():
            form.save()
            return redirect('projetos:kanban')
    else:
        form = AtividadeForm(instance=atividade)
    contexto = {'form': form, 'titulo': 'Editar Atividade', 'voltar_url': reverse_lazy('projetos:kanban')}
    return render(request, 'projetos/atividade_form.html', contexto)


@coordenador_required
def excluir_atividade(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    if request.method == 'POST':
        atividade.delete()
    return redirect('projetos:kanban')


def lista_projetos(request):
    projetos = Projeto.objects.prefetch_related('atividades')
    contexto = {'projetos': projetos}
    return render(request, 'projetos/lista_projetos.html', contexto)


@login_required
def novo_projeto(request):
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('projetos:lista_projetos')
    else:
        form = ProjetoForm()
    contexto = {'form': form, 'titulo': 'Novo Projeto', 'voltar_url': reverse_lazy('projetos:lista_projetos')}
    return render(request, 'projetos/projeto_form.html', contexto)


@login_required
def editar_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        form = ProjetoForm(request.POST, instance=projeto)
        if form.is_valid():
            form.save()
            return redirect('projetos:lista_projetos')
    else:
        form = ProjetoForm(instance=projeto)
    contexto = {'form': form, 'titulo': 'Editar Projeto', 'voltar_url': reverse_lazy('projetos:lista_projetos')}
    return render(request, 'projetos/projeto_form.html', contexto)


@coordenador_required
def excluir_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        projeto.delete()
    return redirect('projetos:lista_projetos')
