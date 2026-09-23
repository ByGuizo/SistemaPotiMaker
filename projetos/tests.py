import shutil
import tempfile
from datetime import date
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from usuarios.models import Usuario

from .forms import AtividadeForm
from .models import Atividade, Projeto

PASTA_MEDIA_TESTE = tempfile.mkdtemp(prefix='potimaker-teste-')


INICIOS = {'.pdf': b'%PDF-1.7\n', '.stl': b'solid peca\n', '.html': b'<html>', '.svg': b'<svg>', '.js': b'alert(1)'}


def _arquivo(nome, tipo, tamanho=100, inicio=None):
    """Arquivo de teste com os primeiros bytes do formato que a extensão diz ser."""
    if inicio is None:
        inicio = INICIOS[Path(nome).suffix.lower()]
    return SimpleUploadedFile(nome, inicio + b'x' * (tamanho - len(inicio)), content_type=tipo)


@override_settings(MEDIA_ROOT=PASTA_MEDIA_TESTE)
class DocumentoTecnicoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA_MEDIA_TESTE, ignore_errors=True)

    def setUp(self):
        self.projeto = Projeto.objects.create(nome='Projeto teste')

    def _form(self, arquivo, instancia=None):
        dados = {'projeto': self.projeto.pk, 'nome': 'Atividade teste', 'prioridade': 'MEDIA'}
        return AtividadeForm(dados, {'documento_tecnico': arquivo}, instance=instancia)

    def test_pdf_valido_e_aceito(self):
        form = self._form(_arquivo('relatorio.pdf', 'application/pdf'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_stl_com_tipo_generico_e_aceito(self):
        form = self._form(_arquivo('peca.STL', 'application/octet-stream'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_html_e_recusado(self):
        form = self._form(_arquivo('pagina.html', 'text/html'))
        self.assertFalse(form.is_valid())
        self.assertIn('documento_tecnico', form.errors)

    def test_svg_e_js_sao_recusados(self):
        for nome, tipo in [('desenho.svg', 'image/svg+xml'), ('script.js', 'text/javascript')]:
            with self.subTest(nome=nome):
                self.assertFalse(self._form(_arquivo(nome, tipo)).is_valid())

    def test_extensao_permitida_com_tipo_html_e_recusada(self):
        form = self._form(_arquivo('pagina.pdf', 'text/html'))
        self.assertFalse(form.is_valid())

    def test_html_renomeado_para_pdf_e_recusado(self):
        """O navegador manda application/pdf pela extensão; quem barra é o conteúdo."""
        html = b'<!DOCTYPE html><script>alert(1)</script>'
        form = self._form(_arquivo('pagina.pdf', 'application/pdf', inicio=html))
        self.assertFalse(form.is_valid())

    def test_svg_renomeado_para_stl_e_recusado(self):
        svg = b'<?xml version="1.0"?><svg onload="alert(1)"/>'
        form = self._form(_arquivo('peca.stl', 'application/octet-stream', inicio=svg))
        self.assertFalse(form.is_valid())

    def test_pdf_com_conteudo_de_outro_formato_e_recusado(self):
        form = self._form(_arquivo('falso.pdf', 'application/pdf', inicio=b'PK\x03\x04'))
        self.assertFalse(form.is_valid())

    def test_docx_com_assinatura_zip_e_aceito(self):
        tipo = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        form = self._form(_arquivo('relatorio.docx', tipo, inicio=b'PK\x03\x04'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_arquivo_acima_de_10mb_e_recusado(self):
        form = self._form(_arquivo('grande.pdf', 'application/pdf', 10 * 1024 * 1024 + 1))
        self.assertFalse(form.is_valid())
        self.assertIn('10 MB', str(form.errors['documento_tecnico']))

    def test_arquivo_de_exatamente_10mb_e_aceito(self):
        form = self._form(_arquivo('limite.pdf', 'application/pdf', 10 * 1024 * 1024))
        self.assertTrue(form.is_valid(), form.errors)

    def test_trocar_documento_apaga_o_antigo_do_disco(self):
        form = self._form(_arquivo('v1.pdf', 'application/pdf'))
        atividade = form.save()
        antigo = Path(atividade.documento_tecnico.path)
        self.assertTrue(antigo.exists())

        with self.captureOnCommitCallbacks(execute=True):
            atividade = self._form(_arquivo('v2.pdf', 'application/pdf'), atividade).save()

        self.assertFalse(antigo.exists())
        self.assertTrue(Path(atividade.documento_tecnico.path).exists())

    def test_troca_recusada_mantem_o_arquivo_antigo(self):
        atividade = self._form(_arquivo('v1.pdf', 'application/pdf')).save()
        antigo = Path(atividade.documento_tecnico.path)

        with self.captureOnCommitCallbacks(execute=True):
            form = self._form(_arquivo('v2.html', 'text/html'), atividade)
            self.assertFalse(form.is_valid())

        self.assertTrue(antigo.exists())

    def test_card_mostra_link_do_documento(self):
        usuario = Usuario.objects.create_user('teste_card', password='x', matricula='T-CARD')
        self.client.force_login(usuario)
        atividade = self._form(_arquivo('manual.pdf', 'application/pdf')).save()
        resposta = self.client.get('/projetos/')
        self.assertContains(resposta, atividade.documento_tecnico.url)
        self.assertContains(resposta, 'Documento técnico')


class OrdemPrioridadeTests(TestCase):
    def test_ordem_alta_media_baixa(self):
        projeto = Projeto.objects.create(nome='Projeto ordem')
        for prioridade in ['BAIXA', 'MEDIA', 'ALTA', 'MEDIA', 'BAIXA', 'ALTA']:
            Atividade.objects.create(projeto=projeto, nome=f'Ativ {prioridade}', prioridade=prioridade)
        ordem = list(Atividade.objects.values_list('prioridade', flat=True))
        self.assertEqual(ordem, ['ALTA', 'ALTA', 'MEDIA', 'MEDIA', 'BAIXA', 'BAIXA'])

    def test_mesma_prioridade_desempata_pelo_prazo(self):
        projeto = Projeto.objects.create(nome='Projeto prazo')
        Atividade.objects.create(projeto=projeto, nome='depois', prioridade='ALTA', prazo=date(2026, 12, 1))
        Atividade.objects.create(projeto=projeto, nome='antes', prioridade='ALTA', prazo=date(2026, 10, 1))
        Atividade.objects.create(projeto=projeto, nome='baixa', prioridade='BAIXA', prazo=date(2026, 1, 1))
        self.assertEqual(list(Atividade.objects.values_list('nome', flat=True)), ['antes', 'depois', 'baixa'])

    def test_valores_gravados_nao_mudam(self):
        projeto = Projeto.objects.create(nome='Projeto valores')
        Atividade.objects.create(projeto=projeto, nome='a', prioridade='MEDIA')
        self.assertEqual(Atividade.objects.get().prioridade, 'MEDIA')

    def test_kanban_mostra_alta_antes_de_media_e_baixa(self):
        usuario = Usuario.objects.create_user('teste_ordem', password='x', matricula='T-ORDEM')
        self.client.force_login(usuario)
        projeto = Projeto.objects.create(nome='Projeto kanban')
        for prioridade in ['BAIXA', 'MEDIA', 'ALTA']:
            Atividade.objects.create(projeto=projeto, nome=f'Card-{prioridade}', prioridade=prioridade)
        html = self.client.get('/projetos/').content.decode()
        self.assertLess(html.index('Card-ALTA'), html.index('Card-MEDIA'))
        self.assertLess(html.index('Card-MEDIA'), html.index('Card-BAIXA'))
