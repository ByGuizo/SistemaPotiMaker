import io
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .forms import PerfilForm
from .models import Usuario

PASTA_MEDIA_TESTE = tempfile.mkdtemp(prefix='potimaker-teste-')


def _png(nome='foto.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (4, 4), 'purple').save(buffer, 'PNG')
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=PASTA_MEDIA_TESTE)
class TrocaFotoPerfilTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA_MEDIA_TESTE, ignore_errors=True)

    def setUp(self):
        self.usuario = Usuario.objects.create_user('teste_foto', password='x', matricula='T-FOTO')

    def _salvar(self, foto):
        form = PerfilForm({'first_name': 'Teste'}, {'foto': foto}, instance=self.usuario)
        self.assertTrue(form.is_valid(), form.errors)
        with self.captureOnCommitCallbacks(execute=True):
            return form.save()

    def test_trocar_foto_apaga_a_antiga(self):
        antiga = Path(self._salvar(_png('a.png')).foto.path)
        nova = Path(self._salvar(_png('b.png')).foto.path)
        self.assertFalse(antiga.exists())
        self.assertTrue(nova.exists())

    def test_salvar_sem_trocar_foto_mantem_o_arquivo(self):
        atual = Path(self._salvar(_png()).foto.path)
        form = PerfilForm({'first_name': 'Outro nome'}, {}, instance=self.usuario)
        self.assertTrue(form.is_valid(), form.errors)
        with self.captureOnCommitCallbacks(execute=True):
            form.save()
        self.assertTrue(atual.exists())
