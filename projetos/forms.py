from pathlib import Path

from django import forms

from core.forms import CampoMembrosWidget, EstiloPotiMakerMixin, SubstituiArquivoMixin

from .models import Atividade, Projeto

# Lista branca: extensão aceita -> content_types que os navegadores costumam
# mandar para ela. "application/octet-stream" (tipo genérico) só vale para os
# formatos que o navegador normalmente não reconhece (STL, ZIP, ODT).
TIPOS_DOCUMENTO = {
    '.pdf': {'application/pdf'},
    '.png': {'image/png'},
    '.jpg': {'image/jpeg', 'image/pjpeg'},
    '.jpeg': {'image/jpeg', 'image/pjpeg'},
    '.docx': {'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
    '.xlsx': {'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
    '.pptx': {'application/vnd.openxmlformats-officedocument.presentationml.presentation'},
    '.odt': {'application/vnd.oasis.opendocument.text', 'application/octet-stream'},
    '.zip': {'application/zip', 'application/x-zip-compressed', 'application/octet-stream'},
    '.stl': {
        'model/stl', 'application/sla', 'application/vnd.ms-pki.stl',
        'application/octet-stream', 'text/plain',
    },
}

# Tipos que o navegador executa ao abrir: nunca aceitos, mesmo com extensão "inocente"
TIPOS_PROIBIDOS = {
    'text/html', 'application/xhtml+xml', 'image/svg+xml',
    'text/javascript', 'application/javascript', 'application/x-javascript',
}

# Primeiros bytes ("assinatura") de cada formato. Extensão e content_type vêm do
# nome do arquivo, então "pagina.html" renomeado para "pagina.pdf" passaria por
# eles; o conteúdo, não. DOCX/XLSX/PPTX/ODT são arquivos ZIP por dentro.
ASSINATURA_ZIP = (b'PK\x03\x04', b'PK\x05\x06')
ASSINATURAS_DOCUMENTO = {
    '.pdf': (b'%PDF-',),
    '.png': (b'\x89PNG\r\n\x1a\n',),
    '.jpg': (b'\xff\xd8\xff',),
    '.jpeg': (b'\xff\xd8\xff',),
    '.docx': ASSINATURA_ZIP,
    '.xlsx': ASSINATURA_ZIP,
    '.pptx': ASSINATURA_ZIP,
    '.odt': ASSINATURA_ZIP,
    '.zip': ASSINATURA_ZIP,
    # STL binário não tem assinatura fixa; só se barra conteúdo com cara de HTML/SVG
    '.stl': None,
}


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


class AtividadeForm(EstiloPotiMakerMixin, SubstituiArquivoMixin, forms.ModelForm):
    TAMANHO_MAX_MB = 10

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
        help_texts = {
            'documento_tecnico': 'PDF, PNG, JPG, DOCX, XLSX, PPTX, ODT, ZIP ou STL de até 10 MB.',
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

    def clean_documento_tecnico(self):
        documento = self.cleaned_data.get('documento_tecnico')
        # Mesmo padrão do PerfilForm.clean_foto: só valida arquivo novo. Sem troca,
        # vem o FieldFile já salvo, que não tem content_type.
        if documento and hasattr(documento, 'content_type'):
            if documento.size > self.TAMANHO_MAX_MB * 1024 * 1024:
                raise forms.ValidationError(
                    f'O documento deve ter no máximo {self.TAMANHO_MAX_MB} MB '
                    f'(o seu tem {documento.size / 1024 / 1024:.1f} MB).'
                )
            extensao = Path(documento.name).suffix.lower()
            tipo = (documento.content_type or '').split(';')[0].strip().lower()
            if (
                extensao not in TIPOS_DOCUMENTO
                or tipo in TIPOS_PROIBIDOS
                or tipo not in TIPOS_DOCUMENTO[extensao]
                or not self._conteudo_confere(documento, extensao)
            ):
                raise forms.ValidationError(
                    'Tipo de arquivo não permitido. Use PDF, PNG, JPG, DOCX, XLSX, PPTX, ODT, ZIP ou STL.'
                )
        return documento

    @staticmethod
    def _conteudo_confere(documento, extensao):
        """Confere se os primeiros bytes do arquivo batem com a extensão."""
        documento.seek(0)
        inicio = documento.read(512)
        documento.seek(0)
        if inicio.lstrip(b'\xef\xbb\xbf \t\r\n').startswith(b'<'):
            return False  # HTML, SVG ou XML disfarçado
        assinaturas = ASSINATURAS_DOCUMENTO[extensao]
        return assinaturas is None or inicio.startswith(assinaturas)
