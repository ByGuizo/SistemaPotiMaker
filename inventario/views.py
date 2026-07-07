from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from usuarios.decorators import coordenador_required

from .forms import ItemForm
from .models import Item


def lista_itens(request):
    termo = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '')
    status = request.GET.get('status', '')

    itens = Item.objects.all()
    if termo:
        itens = itens.filter(nome__icontains=termo)
    if categoria:
        itens = itens.filter(categoria=categoria)
    if status:
        itens = itens.filter(status=status)

    contexto = {
        'itens': itens,
        'termo': termo,
        'categoria': categoria,
        'status': status,
        'categorias': Item.Categoria.choices,
        'status_choices': Item.Status.choices,
    }
    template = 'inventario/partials/_tabela_itens.html' if request.headers.get('HX-Request') else 'inventario/lista.html'
    return render(request, template, contexto)


@login_required
def novo_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventario:lista_itens')
    else:
        form = ItemForm()
    contexto = {'form': form, 'titulo': 'Adicionar Item', 'voltar_url': reverse_lazy('inventario:lista_itens')}
    return render(request, 'inventario/item_form.html', contexto)


@login_required
def editar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('inventario:lista_itens')
    else:
        form = ItemForm(instance=item)
    contexto = {'form': form, 'titulo': 'Editar Item', 'voltar_url': reverse_lazy('inventario:lista_itens')}
    return render(request, 'inventario/item_form.html', contexto)


@coordenador_required
def excluir_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
    return redirect('inventario:lista_itens')
