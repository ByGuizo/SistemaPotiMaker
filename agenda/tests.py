from django.test import TestCase

from usuarios.models import Usuario


class PainelDiaTests(TestCase):
    def setUp(self):
        usuario = Usuario.objects.create_user('teste_agenda', password='x', matricula='T-AGENDA')
        self.client.force_login(usuario)

    def test_data_valida(self):
        self.assertEqual(self.client.get('/agenda/dia/2026/10/14/').status_code, 200)

    def test_data_inexistente_retorna_404(self):
        self.assertEqual(self.client.get('/agenda/dia/2026/2/30/').status_code, 404)

    def test_numero_gigante_retorna_404(self):
        for url in ['/agenda/dia/99999999999999999999/1/1/', '/agenda/dia/2026/1/99999999999999999999/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
