import json

from django import forms
from django.db import models, transaction
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


class SubstituiArquivoMixin:
    """
    Apaga do disco o arquivo antigo quando um campo de arquivo (FileField ou
    ImageField) é trocado ou limpo no formulário.

    O Django não faz isso sozinho: sem este mixin, cada troca de foto deixa
    o arquivo anterior esquecido em media/. A remoção só acontece depois que o
    registro com o arquivo novo foi gravado no banco (transaction.on_commit) —
    se algo falhar antes, o arquivo antigo continua lá e ainda é o válido.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._arquivos_antigos = {
            campo.name: getattr(self.instance, campo.name).name
            for campo in self.instance._meta.get_fields()
            if isinstance(campo, models.FileField) and campo.name in self.fields
        }

    def save(self, commit=True):
        objeto = super().save(commit=commit)
        if commit:
            for nome_campo, antigo in self._arquivos_antigos.items():
                arquivo = getattr(objeto, nome_campo)
                if antigo and antigo != arquivo.name:
                    storage = arquivo.storage
                    transaction.on_commit(lambda s=storage, n=antigo: s.delete(n))
        return objeto


class EstiloPotiMakerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            # O campo de membros tem estilo próprio (.ms-*), não usa INPUT_CLASS
            if isinstance(field.widget, CampoMembrosWidget):
                continue
            existente = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existente} {INPUT_CLASS}'.strip()
