from django import forms

from core.forms import EstiloPotiMakerMixin

from .models import Item


class ItemForm(EstiloPotiMakerMixin, forms.ModelForm):
    class Meta:
        model = Item
        fields = ['nome', 'categoria', 'quantidade', 'status']
        labels = {
            'nome': 'Item',
            'categoria': 'Categoria',
            'quantidade': 'Quantidade',
            'status': 'Status',
        }
