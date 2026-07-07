from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from usuarios.decorators import coordenador_required

from .forms import ProjetoForm
from .models import Projeto


def kanban(request):
    colunas = []
    for status_valor, status_label in Projeto.Status.choices:
        projetos = Projeto.objects.filter(status=status_valor).prefetch_related('membros')
        colunas.append({'valor': status_valor, 'label': status_label, 'projetos': projetos})

    contexto = {'colunas': colunas}
    template = 'projetos/partials/_kanban_colunas.html' if request.headers.get('HX-Request') else 'projetos/kanban.html'
    return render(request, template, contexto)


@login_required
def mover_projeto(request, pk, direcao):
    if request.method == 'POST':
        projeto = get_object_or_404(Projeto, pk=pk)
        projeto.mover(direcao)
    return kanban(request)


@login_required
def novo_projeto(request):
    if request.method == 'POST':
        form = ProjetoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('projetos:kanban')
    else:
        form = ProjetoForm()
    contexto = {'form': form, 'titulo': 'Novo Projeto', 'voltar_url': reverse_lazy('projetos:kanban')}
    return render(request, 'projetos/projeto_form.html', contexto)


@login_required
def editar_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        form = ProjetoForm(request.POST, request.FILES, instance=projeto)
        if form.is_valid():
            form.save()
            return redirect('projetos:kanban')
    else:
        form = ProjetoForm(instance=projeto)
    contexto = {'form': form, 'titulo': 'Editar Projeto', 'voltar_url': reverse_lazy('projetos:kanban')}
    return render(request, 'projetos/projeto_form.html', contexto)


@coordenador_required
def excluir_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        projeto.delete()
    return redirect('projetos:kanban')
