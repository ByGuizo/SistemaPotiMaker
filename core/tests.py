import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings

from usuarios.models import Usuario

PASTA_MEDIA_TESTE = tempfile.mkdtemp(prefix='potimaker-teste-')


@override_settings(MEDIA_ROOT=PASTA_MEDIA_TESTE)
class ServirMediaTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raiz = Path(PASTA_MEDIA_TESTE)
        (raiz / 'perfis').mkdir(exist_ok=True)
        (raiz / 'projetos' / 'docs').mkdir(parents=True, exist_ok=True)
        (raiz / 'perfis' / 'foto.png').write_bytes(b'\x89PNG teste')
        (raiz / 'projetos' / 'docs' / 'manual.pdf').write_bytes(b'%PDF teste')
        # Arquivo "secreto" fora da media, vizinho da pasta temporária
        cls.segredo = raiz.parent / f'{raiz.name}-segredo.txt'
        cls.segredo.write_text('nao deveria vazar')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.segredo.unlink(missing_ok=True)
        shutil.rmtree(PASTA_MEDIA_TESTE, ignore_errors=True)

    def setUp(self):
        self.usuario = Usuario.objects.create_user('teste_media', password='x', matricula='T-MEDIA')

    def test_visitante_sem_login_e_redirecionado(self):
        resposta = self.client.get('/media/perfis/foto.png')
        self.assertEqual(resposta.status_code, 302)
        self.assertIn('/usuarios/login/', resposta['Location'])

    def test_logado_recebe_foto_inline(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get('/media/perfis/foto.png')
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta['Content-Disposition'].startswith('inline'))
        self.assertEqual(b''.join(resposta.streaming_content), b'\x89PNG teste')

    def test_documento_sai_como_download(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get('/media/projetos/docs/manual.pdf')
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta['Content-Disposition'].startswith('attachment'))
        self.assertIn("sandbox", resposta['Content-Security-Policy'])

    def test_path_traversal_retorna_404(self):
        self.client.force_login(self.usuario)
        nome_segredo = self.segredo.name
        for caminho in [
            f'/media/../{nome_segredo}',
            f'/media/perfis/../../{nome_segredo}',
            f'/media/%2e%2e/{nome_segredo}',
            f'/media/perfis/..%2f..%2f{nome_segredo}',
            f'/media/{self.segredo.as_posix()}',
        ]:
            with self.subTest(caminho=caminho):
                self.assertEqual(self.client.get(caminho).status_code, 404)

    def test_arquivo_inexistente_e_pasta_retornam_404(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get('/media/perfis/nao-existe.png').status_code, 404)
        self.assertEqual(self.client.get('/media/perfis/').status_code, 404)


class ConfiguracaoProducaoTests(SimpleTestCase):
    """
    O settings.py só é lido quando o Django inicia, então cada cenário roda o
    manage.py num processo separado, com as variáveis de ambiente do cenário.
    """

    CHAVE_LONGA = 'chave-de-teste-' + 'x' * 60

    def _rodar(self, *args, **variaveis):
        ambiente = {
            k: v for k, v in os.environ.items()
            if not k.startswith('DJANGO_')
        }
        # Sem isso, no Windows o filho escreve em cp1252 e os acentos da
        # mensagem de erro quebram a leitura da saída
        ambiente['PYTHONIOENCODING'] = 'utf-8'
        ambiente.update(variaveis)
        return subprocess.run(
            [sys.executable, 'manage.py', *args],
            cwd=settings.BASE_DIR, env=ambiente,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
        )

    def test_producao_sem_secret_key_nao_inicia(self):
        # Vazia (e não ausente) para o .env local não conseguir preenchê-la
        resultado = self._rodar('check', DJANGO_DEBUG='False', DJANGO_SECRET_KEY='')
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY', resultado.stderr)

    def test_check_deploy_so_avisa_do_hsts(self):
        resultado = self._rodar(
            'check', '--deploy',
            DJANGO_DEBUG='False',
            DJANGO_SECRET_KEY=self.CHAVE_LONGA,
            DJANGO_ALLOWED_HOSTS='potimaker.exemplo.ifrn.edu.br',
        )
        saida = resultado.stdout + resultado.stderr
        self.assertIn('security.W004', saida)
        self.assertIn('1 issue', saida)


class BackupBancoTests(TransactionTestCase):
    """
    TransactionTestCase: os dados do teste são gravados de verdade (no banco de
    teste), como aconteceria com o sistema rodando. O banco real não é tocado.
    """

    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix='potimaker-backup-'))
        self.addCleanup(shutil.rmtree, self.pasta, ignore_errors=True)
        ajuste = override_settings(BACKUP_DIR=self.pasta)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

    def _backups(self):
        return sorted(self.pasta.glob('db_*.sqlite3'))

    def test_backup_contem_os_dados_e_passa_na_integridade(self):
        Usuario.objects.create_user('zz_backup', password='x', matricula='T-BACKUP')
        call_command('backup_banco', stdout=StringIO())

        backups = self._backups()
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as copia:
            self.assertEqual(copia.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            nomes = [r[0] for r in copia.execute('SELECT username FROM usuarios_usuario')]
        self.assertIn('zz_backup', nomes)
        self.assertEqual(list(self.pasta.glob('*.parcial')), [])

    def test_nome_tem_data_e_hora(self):
        call_command('backup_banco', stdout=StringIO())
        self.assertRegex(self._backups()[0].name, r'^db_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.sqlite3$')

    def test_mantem_so_os_n_mais_recentes(self):
        for dia in range(1, 6):
            (self.pasta / f'db_2020-01-0{dia}_03-00-00.sqlite3').write_bytes(b'antigo')
        outro_arquivo = self.pasta / 'anotacoes.txt'
        outro_arquivo.write_text('não é backup')

        call_command('backup_banco', manter=3, stdout=StringIO())

        nomes = [b.name for b in self._backups()]
        self.assertEqual(len(nomes), 3)
        self.assertEqual(nomes[:2], ['db_2020-01-04_03-00-00.sqlite3', 'db_2020-01-05_03-00-00.sqlite3'])
        self.assertFalse(nomes[2].startswith('db_2020'))  # o novo foi mantido
        self.assertTrue(outro_arquivo.exists())  # só mexe nos arquivos db_*.sqlite3

    def test_manter_zero_e_recusado_sem_apagar_nada(self):
        antigo = self.pasta / 'db_2020-01-01_03-00-00.sqlite3'
        antigo.write_bytes(b'antigo')
        with self.assertRaises(CommandError):
            call_command('backup_banco', manter=0, stdout=StringIO())
        self.assertTrue(antigo.exists())
