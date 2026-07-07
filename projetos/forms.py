from django import forms

from core.forms import EstiloPotiMakerMixin

from .models import Projeto


class ProjetoForm(EstiloPotiMakerMixin, forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['nome', 'descricao', 'documento_tecnico', 'prioridade', 'prazo', 'membros']
        labels = {
            'nome': 'Nome do projeto',
            'descricao': 'Descrição',
            'documento_tecnico': 'Documento técnico',
            'prioridade': 'Prioridade',
            'prazo': 'Prazo',
            'membros': 'Membros responsáveis',
        }
        widgets = {
            'prazo': forms.DateInput(attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }
