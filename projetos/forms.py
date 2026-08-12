from django import forms

from core.forms import CampoMembrosWidget, EstiloPotiMakerMixin

from .models import Atividade, Projeto


class ProjetoForm(EstiloPotiMakerMixin, forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome do projeto',
            'descricao': 'Descrição',
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }


class AtividadeForm(EstiloPotiMakerMixin, forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['projeto', 'nome', 'descricao', 'documento_tecnico', 'prioridade', 'prazo', 'membros']
        labels = {
            'projeto': 'Projeto',
            'nome': 'Nome da atividade',
            'descricao': 'Descrição',
            'documento_tecnico': 'Documento técnico',
            'prioridade': 'Prioridade',
            'prazo': 'Prazo',
            'membros': 'Membros responsáveis',
        }
        widgets = {
            'prazo': forms.DateInput(attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'membros': CampoMembrosWidget,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só membros aprovados podem ser responsáveis por uma atividade
        self.fields['membros'].queryset = self.fields['membros'].queryset.filter(
            is_active=True
        ).order_by('first_name', 'username')
