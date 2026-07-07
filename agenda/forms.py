from django import forms

from core.forms import EstiloPotiMakerMixin

from .models import Evento


class EventoForm(EstiloPotiMakerMixin, forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'descricao', 'data', 'hora_inicio', 'hora_fim', 'local']
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'data': 'Data',
            'hora_inicio': 'Hora de início',
            'hora_fim': 'Hora de término',
            'local': 'Local',
        }
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }
