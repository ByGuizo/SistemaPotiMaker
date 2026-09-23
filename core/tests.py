import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


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
        ambiente.update(variaveis)
        return subprocess.run(
            [sys.executable, 'manage.py', *args],
            cwd=settings.BASE_DIR, env=ambiente,
            capture_output=True, text=True, encoding='utf-8',
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
