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

    def clean(self):
        dados = super().clean()
        inicio = dados.get('hora_inicio')
        fim = dados.get('hora_fim')
        # Ambos são opcionais; só valida a ordem quando os dois foram informados
        if inicio and fim and fim <= inicio:
            self.add_error('hora_fim', 'A hora de término deve ser depois da hora de início.')
        return dados
