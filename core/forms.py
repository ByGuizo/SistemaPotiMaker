import json

from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe

INPUT_CLASS = (
    'w-full border-2 border-black px-3 py-2 transition-all duration-150 '
    'focus:outline-none focus:shadow-brutal-fuchsia focus:-translate-x-0.5 focus:-translate-y-0.5'
)


class CampoMembrosWidget(forms.SelectMultiple):
    """
    Renderiza um ManyToMany no formato que o static/js/multi-select.js espera:
    digita-se o nome, ele completa inline e Enter/Tab adiciona como chip.

    Mantém um <noscript> com o <select multiple> nativo, então o formulário
    continua utilizável sem JS — e o POST tem o mesmo formato nos dois casos.
    """

    placeholder = 'Digite um nome...'

    class Media:
        js = ('js/multi-select.js?v=4',)

    def render(self, name, value, attrs=None, renderer=None):
        selecionados = {str(v) for v in (value or []) if v is not None}

        opcoes = []
        for grupo, escolhas, indice in self.optgroups(name, list(selecionados), attrs):
            for escolha in escolhas:
                if escolha['value'] in ('', None):
                    continue
                opcoes.append({
                    'id': str(escolha['value']),
                    'texto': str(escolha['label']),
                    'selecionado': str(escolha['value']) in selecionados,
                })

        # O <select> do noscript reaproveita o render nativo do SelectMultiple
        nativo = super().render(name, value, attrs, renderer)

        # Escapa < > & para que um nome contendo "</script>" não feche a tag
        dados = (
            json.dumps(opcoes, ensure_ascii=False)
            .replace('<', '\\u003c')
            .replace('>', '\\u003e')
            .replace('&', '\\u0026')
        )

        return format_html(
            '<div class="multi-select" data-nome="{}" data-placeholder="{}">'
            '<script type="application/json" class="multi-select-dados">{}</script>'
            '</div><noscript>{}</noscript>',
            name,
            self.placeholder,
            mark_safe(dados),
            nativo,
        )


class EstiloPotiMakerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            # O campo de membros tem estilo próprio (.ms-*), não usa INPUT_CLASS
            if isinstance(field.widget, CampoMembrosWidget):
                continue
            existente = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existente} {INPUT_CLASS}'.strip()
