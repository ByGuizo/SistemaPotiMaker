from django.test import TestCase

from usuarios.models import Usuario

from .models import Item


class PermissoesInventarioTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(nome='Impressora 3D', categoria=Item.Categoria.EQUIPAMENTO, quantidade=1)
        self.membro = Usuario.objects.create_user('membro_inv', password='x', matricula='T-INV1')
        self.coord = Usuario.objects.create_user(
            'coord_inv', password='x', matricula='T-INV2', tipo=Usuario.Tipo.COORDENADOR,
        )

    def test_membro_edita_item(self):
        self.client.force_login(self.membro)
        resposta = self.client.post(f'/inventario/{self.item.pk}/editar/', {
            'nome': 'Impressora 3D Ender', 'categoria': 'EQUIPAMENTO', 'quantidade': 2, 'status': 'DISPONIVEL',
        })
        self.assertEqual(resposta.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade, 2)

    def test_membro_nao_exclui_item(self):
        self.client.force_login(self.membro)
        self.assertEqual(self.client.post(f'/inventario/{self.item.pk}/excluir/').status_code, 403)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_coordenador_exclui_item(self):
        self.client.force_login(self.coord)
        self.client.post(f'/inventario/{self.item.pk}/excluir/')
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_exclusao_por_get_nao_apaga(self):
        self.client.force_login(self.coord)
        self.client.get(f'/inventario/{self.item.pk}/excluir/')
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_visitante_e_redirecionado_para_o_login(self):
        resposta = self.client.get('/inventario/')
        self.assertEqual(resposta.status_code, 302)
        self.assertIn('/usuarios/login/', resposta['Location'])
