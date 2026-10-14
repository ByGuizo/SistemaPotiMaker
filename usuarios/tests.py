import io
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from .forms import CadastroForm, MembroForm, PerfilForm
from .models import HorarioEscala, Usuario

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


def _criar(username, tipo=Usuario.Tipo.MEMBRO, pendente=False, ativo=True):
    usuario = Usuario.objects.create_user(
        username, password='Senha-Forte-2026!', matricula=f'T-{username}',
        first_name=username.title(), tipo=tipo,
    )
    if pendente:
        usuario.status_cadastro = Usuario.StatusCadastro.PENDENTE
        usuario.is_active = False
    else:
        usuario.is_active = ativo
    usuario.save()
    return usuario


class EditarHorariosTests(TestCase):
    URL = '/usuarios/horarios/editar/'

    def setUp(self):
        self.coord = _criar('coord_escala', tipo=Usuario.Tipo.COORDENADOR)
        self.membro = _criar('membro_escala')
        self.client.force_login(self.coord)

    def _membros_da_celula(self, dia=0, slot='M1'):
        return set(HorarioEscala.objects.get(dia_semana=dia, slot=slot).membros.values_list('pk', flat=True))

    def test_id_valido_e_gravado(self):
        resposta = self.client.post(self.URL, {'celula_0_M1': [self.membro.pk]})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self._membros_da_celula(), {self.membro.pk})

    def test_id_invalido_e_ignorado_sem_erro_500(self):
        lixo = ['abc', '', '1.5', '-', '9' * 5000, str(self.membro.pk)]
        resposta = self.client.post(self.URL, {'celula_0_M1': lixo})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self._membros_da_celula(), {self.membro.pk})

    def test_id_de_pendente_e_ignorado(self):
        pendente = _criar('pendente_escala', pendente=True)
        self.client.post(self.URL, {'celula_0_M1': [pendente.pk, self.membro.pk]})
        self.assertEqual(self._membros_da_celula(), {self.membro.pk})

    def test_id_de_inativo_e_ignorado(self):
        inativo = _criar('inativo_escala', ativo=False)
        self.client.post(self.URL, {'celula_0_M1': [inativo.pk]})
        self.assertEqual(self._membros_da_celula(), set())

    def test_id_inexistente_e_ignorado(self):
        resposta = self.client.post(self.URL, {'celula_0_M1': [999999, self.membro.pk]})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self._membros_da_celula(), {self.membro.pk})

    def test_falha_no_meio_nao_grava_pela_metade(self):
        """transaction.atomic(): se a 10ª célula falha, as 9 primeiras voltam atrás."""
        self.client.post(self.URL, {'celula_0_M1': [self.coord.pk]})
        original = HorarioEscala.objects.get_or_create
        chamadas = {'n': 0}

        def falha_na_decima(*args, **kwargs):
            chamadas['n'] += 1
            if chamadas['n'] == 10:
                raise RuntimeError('falha simulada')
            return original(*args, **kwargs)

        with patch.object(HorarioEscala.objects, 'get_or_create', side_effect=falha_na_decima):
            with self.assertRaises(RuntimeError), self.assertLogs('django.request', 'ERROR'):
                self.client.post(self.URL, {'celula_0_M1': [self.membro.pk]})
        self.assertEqual(self._membros_da_celula(), {self.coord.pk})

    def test_membro_comum_nao_edita_a_escala(self):
        self.client.force_login(self.membro)
        self.assertEqual(self.client.post(self.URL, {}).status_code, 403)


class GestaoMembrosTests(TestCase):
    def setUp(self):
        self.coord = _criar('coord_gestao', tipo=Usuario.Tipo.COORDENADOR)
        self.membro = _criar('membro_gestao')
        self.client.force_login(self.coord)

    @staticmethod
    def _dados(usuario, **mudancas):
        """POST do formulário de membro. is_active=None = caixa "Ativo" desmarcada."""
        dados = {
            'first_name': usuario.first_name, 'username': usuario.username,
            'matricula': usuario.matricula, 'tipo': usuario.tipo, 'is_active': 'on',
            'password': '',
        }
        dados.update(mudancas)
        return {k: v for k, v in dados.items() if v is not None}

    def _editar(self, usuario, **mudancas):
        return self.client.post(f'/usuarios/membros/{usuario.pk}/editar/', self._dados(usuario, **mudancas))

    # --- Cadastro pendente fica fora desta tela ---
    def test_pendente_nao_abre_na_edicao(self):
        pendente = _criar('pendente_gestao', pendente=True)
        self.assertEqual(self.client.get(f'/usuarios/membros/{pendente.pk}/editar/').status_code, 404)

    def test_pendente_nao_e_ativado_pela_edicao(self):
        pendente = _criar('pendente_gestao2', pendente=True)
        self.assertEqual(self._editar(pendente).status_code, 404)
        pendente.refresh_from_db()
        self.assertFalse(pendente.is_active)
        self.assertTrue(pendente.is_pendente)

    def test_pendente_nao_e_excluido_por_esta_tela(self):
        pendente = _criar('pendente_gestao3', pendente=True)
        self.assertEqual(self.client.post(f'/usuarios/membros/{pendente.pk}/excluir/').status_code, 404)
        self.assertTrue(Usuario.objects.filter(pk=pendente.pk).exists())

    # --- Senha definida pelo coordenador ---
    def test_senha_fraca_e_recusada(self):
        for senha in ['123', '12345678', 'password']:
            with self.subTest(senha=senha):
                resposta = self._editar(self.membro, password=senha)
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].errors.get('password'))
        self.membro.refresh_from_db()
        self.assertTrue(self.membro.check_password('Senha-Forte-2026!'))

    def test_senha_forte_e_aceita(self):
        self.assertEqual(self._editar(self.membro, password='Outra-Senha-Forte-99').status_code, 302)
        self.membro.refresh_from_db()
        self.assertTrue(self.membro.check_password('Outra-Senha-Forte-99'))

    def test_senha_em_branco_mantem_a_atual(self):
        self.assertEqual(self._editar(self.membro, first_name='Novo Nome').status_code, 302)
        self.membro.refresh_from_db()
        self.assertTrue(self.membro.check_password('Senha-Forte-2026!'))

    # --- Último coordenador ativo ---
    def test_ultimo_coordenador_nao_se_rebaixa(self):
        resposta = self._editar(self.coord, tipo=Usuario.Tipo.MEMBRO)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('último coordenador ativo', str(resposta.context['form'].errors['tipo']))
        self.coord.refresh_from_db()
        self.assertTrue(self.coord.is_coordenador)

    def test_formulario_nao_desativa_nem_rebaixa_o_ultimo_coordenador(self):
        """Direto no MembroForm, sem editor: vale para qualquer uso futuro do formulário."""
        dados = self._dados(self.coord, tipo=Usuario.Tipo.MEMBRO, is_active=None)
        form = MembroForm(dados, instance=self.coord)
        self.assertFalse(form.is_valid())
        self.assertIn('último coordenador ativo', str(form.errors['is_active']))
        self.assertIn('último coordenador ativo', str(form.errors['tipo']))

    def test_regra_do_ultimo_coordenador_no_model(self):
        self.assertTrue(self.coord.e_ultimo_coordenador_ativo())
        self.assertFalse(self.membro.e_ultimo_coordenador_ativo())
        _criar('coord_inativo', tipo=Usuario.Tipo.COORDENADOR, ativo=False)
        _criar('coord_pendente', tipo=Usuario.Tipo.COORDENADOR, pendente=True)
        self.assertTrue(self.coord.e_ultimo_coordenador_ativo())  # inativo e pendente não contam
        _criar('coord_segundo', tipo=Usuario.Tipo.COORDENADOR)
        self.assertFalse(self.coord.e_ultimo_coordenador_ativo())

    def test_ultimo_coordenador_nao_e_excluido(self):
        with patch.object(Usuario, 'e_ultimo_coordenador_ativo', return_value=True):
            resposta = self.client.post(f'/usuarios/membros/{self.membro.pk}/excluir/', follow=True)
        self.assertTrue(Usuario.objects.filter(pk=self.membro.pk).exists())
        self.assertContains(resposta, 'último coordenador ativo')

    def test_com_dois_coordenadores_pode_rebaixar_e_excluir_um(self):
        outro = _criar('coord_extra', tipo=Usuario.Tipo.COORDENADOR)
        self.assertEqual(self._editar(outro, tipo=Usuario.Tipo.MEMBRO).status_code, 302)
        outro.refresh_from_db()
        self.assertFalse(outro.is_coordenador)
        terceiro = _criar('coord_extra2', tipo=Usuario.Tipo.COORDENADOR)
        self.client.post(f'/usuarios/membros/{terceiro.pk}/excluir/')
        self.assertFalse(Usuario.objects.filter(pk=terceiro.pk).exists())

    # --- Própria conta ---
    def test_nao_desativa_a_propria_conta(self):
        _criar('coord_reserva', tipo=Usuario.Tipo.COORDENADOR)  # não é o último
        resposta = self._editar(self.coord, is_active=None)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('própria conta', str(resposta.context['form'].errors['is_active']))
        self.coord.refresh_from_db()
        self.assertTrue(self.coord.is_active)

    def test_nao_exclui_a_propria_conta(self):
        _criar('coord_reserva2', tipo=Usuario.Tipo.COORDENADOR)
        resposta = self.client.post(f'/usuarios/membros/{self.coord.pk}/excluir/', follow=True)
        self.assertTrue(Usuario.objects.filter(pk=self.coord.pk).exists())
        self.assertContains(resposta, 'própria conta')

    def test_membro_comum_pode_ser_desativado(self):
        self.assertEqual(self._editar(self.membro, is_active=None).status_code, 302)
        self.membro.refresh_from_db()
        self.assertFalse(self.membro.is_active)


class UsernameSemMaiusculasTests(TestCase):
    def setUp(self):
        self.existente = _criar('Guizo_Teste')

    def _cadastro(self, username):
        return CadastroForm({
            'first_name': 'Fulano', 'username': username, 'matricula': f'M-{username}',
            'password': 'Senha-Forte-2026!', 'password_confirmacao': 'Senha-Forte-2026!',
        })

    def _edicao(self, usuario, username):
        return MembroForm({
            'first_name': 'X', 'username': username, 'matricula': usuario.matricula,
            'tipo': Usuario.Tipo.MEMBRO, 'is_active': True,
        }, instance=usuario)

    def test_cadastro_recusa_mesmo_nome_com_outra_caixa(self):
        for nome in ['guizo_teste', 'GUIZO_TESTE', 'Guizo_Teste']:
            with self.subTest(nome=nome):
                form = self._cadastro(nome)
                self.assertFalse(form.is_valid())
                self.assertIn('username', form.errors)

    def test_cadastro_aceita_nome_diferente(self):
        self.assertTrue(self._cadastro('outro_nome').is_valid())

    def test_edicao_recusa_nome_de_outro_usuario(self):
        form = self._edicao(_criar('membro_nome'), 'GUIZO_teste')
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_edicao_aceita_mudar_a_caixa_do_proprio_nome(self):
        form = self._edicao(self.existente, 'guizo_teste')
        self.assertTrue(form.is_valid(), form.errors)


class BloqueioLoginTests(TestCase):
    URL = '/usuarios/login/'
    SENHA = 'Senha-Forte-2026!'

    def setUp(self):
        self.maria = _criar('maria_login')

    def _login(self, senha, username='maria_login', ip='10.0.0.1'):
        return self.client.post(self.URL, {'username': username, 'password': senha}, REMOTE_ADDR=ip)

    def _errar(self, vezes, **kwargs):
        for _ in range(vezes):
            self.assertEqual(self._login('senha-errada', **kwargs).status_code, 200)

    def _bloquear(self, **kwargs):
        """4 erros normais; o 5º já recebe a tela de bloqueio."""
        self._errar(4, **kwargs)
        self.assertEqual(self._login('senha-errada', **kwargs).status_code, 429)

    def _logado(self):
        return '_auth_user_id' in self.client.session

    def test_quatro_erros_ainda_permitem_entrar(self):
        self._errar(4)
        self.assertEqual(self._login(self.SENHA).status_code, 302)
        self.assertTrue(self._logado())

    def test_cinco_erros_bloqueiam_mesmo_com_a_senha_certa(self):
        self._bloquear()
        resposta = self._login(self.SENHA)
        self.assertEqual(resposta.status_code, 429)
        self.assertContains(resposta, 'bloqueado por 15 minutos', status_code=429)
        self.assertFalse(self._logado())

    def test_bloqueio_vale_para_a_combinacao_usuario_e_ip(self):
        self._bloquear(ip='10.0.0.1')
        # Mesmo usuário, outro IP: entra
        self.assertEqual(self._login(self.SENHA, ip='10.0.0.2').status_code, 302)
        self.client.logout()
        # Outro usuário, mesmo IP: entra
        _criar('joao_login')
        self.assertEqual(self._login(self.SENHA, username='joao_login', ip='10.0.0.1').status_code, 302)

    def test_variar_maiusculas_nao_da_tentativas_extras(self):
        for nome in ['MARIA_LOGIN', 'Maria_Login', 'maria_LOGIN', 'mAria_login', 'maria_login']:
            self._login('senha-errada', username=nome)
        self.assertEqual(self._login(self.SENHA).status_code, 429)

    def test_bloqueio_expira_depois_de_15_minutos(self):
        from axes.models import AccessAttempt

        self._bloquear()
        self.assertEqual(self._login(self.SENHA).status_code, 429)
        AccessAttempt.objects.update(attempt_time=timezone.now() - timedelta(minutes=16))
        self.assertEqual(self._login(self.SENHA).status_code, 302)

    def test_login_certo_zera_o_contador(self):
        self._errar(4)
        self._login(self.SENHA)
        self.client.logout()
        self._errar(4)
        self.assertEqual(self._login(self.SENHA).status_code, 302)

    def test_pendente_continua_vendo_aguardando_aprovacao(self):
        pendente = _criar('pendente_login', pendente=True)
        self._errar(3, username=pendente.username)
        resposta = self._login(self.SENHA, username=pendente.username)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'aguardando a aprovação')
        self.assertFalse(self._logado())

    def test_pendente_com_senha_errada_nao_revela_o_status(self):
        pendente = _criar('pendente_login2', pendente=True)
        resposta = self._login('senha-errada', username=pendente.username)
        self.assertNotContains(resposta, 'aguardando a aprovação')

    def test_ip_real_so_e_lido_do_nginx_quando_configurado(self):
        from django.test import RequestFactory

        from .seguranca import ip_do_cliente

        request = RequestFactory().get('/', REMOTE_ADDR='127.0.0.1', HTTP_X_REAL_IP='200.1.2.3')
        with self.settings(CONFIAR_X_REAL_IP=False):
            self.assertEqual(ip_do_cliente(request), '127.0.0.1')
        with self.settings(CONFIAR_X_REAL_IP=True):
            self.assertEqual(ip_do_cliente(request), '200.1.2.3')


class LimiteCadastroTests(TestCase):
    URL = '/usuarios/cadastro/'

    def setUp(self):
        cache.clear()

    def _cadastrar(self, n, ip='10.0.0.1', **extra):
        dados = {
            'first_name': f'Pessoa {n}', 'username': f'pessoa_{n}', 'matricula': f'MAT-{n}',
            'password': 'Senha-Forte-2026!', 'password_confirmacao': 'Senha-Forte-2026!',
        }
        dados.update(extra)
        return self.client.post(self.URL, dados, REMOTE_ADDR=ip)

    def test_sexto_cadastro_na_mesma_hora_e_recusado(self):
        for n in range(5):
            self.assertEqual(self._cadastrar(n).status_code, 302)
        resposta = self._cadastrar(5)
        self.assertEqual(resposta.status_code, 429)
        self.assertContains(resposta, 'muitos cadastros', status_code=429)
        self.assertFalse(Usuario.objects.filter(username='pessoa_5').exists())

    def test_limite_e_por_ip(self):
        for n in range(5):
            self._cadastrar(n)
        self.assertEqual(self._cadastrar(5, ip='10.0.0.2').status_code, 302)
        self.assertTrue(Usuario.objects.filter(username='pessoa_5').exists())

    def test_formulario_com_erro_nao_conta_no_limite(self):
        for n in range(6):
            self._cadastrar(n, password_confirmacao='diferente')
        self.assertEqual(self._cadastrar(99).status_code, 302)

    def test_honeypot_preenchido_nao_cria_usuario(self):
        resposta = self._cadastrar(1, website='http://spam.example')
        self.assertEqual(resposta.status_code, 302)  # parece sucesso para o robô
        self.assertFalse(Usuario.objects.filter(username='pessoa_1').exists())

    def test_honeypot_esta_escondido_na_pagina(self):
        html = self.client.get(self.URL).content.decode()
        self.assertIn('name="website"', html)
        self.assertIn('left:-10000px', html)
        self.assertIn('tabindex="-1"', html)


class LattesTests(TestCase):
    def setUp(self):
        self.usuario = _criar('teste_lattes')

    def _form(self, url):
        return PerfilForm({'first_name': 'Teste', 'lattes': url}, {}, instance=self.usuario)

    def test_endereco_do_lattes_e_aceito(self):
        for url in ['http://lattes.cnpq.br/1234567890123456', 'https://wwws.lattes.cnpq.br/cv/123']:
            with self.subTest(url=url):
                self.assertTrue(self._form(url).is_valid())

    def test_outro_dominio_e_recusado(self):
        for url in [
            'https://site-falso.com/?lattes.cnpq.br',
            'https://lattes.cnpq.br.site-falso.com/123',
            'https://site-falso.com/lattes.cnpq.br/123',
            'ftp://lattes.cnpq.br/123',
            'javascript:alert(1)//lattes.cnpq.br',
        ]:
            with self.subTest(url=url):
                self.assertFalse(self._form(url).is_valid())


class EditarPerfilTests(TestCase):
    def test_formulario_com_erro_nao_altera_o_usuario_logado(self):
        usuario = _criar('teste_perfil')
        self.client.force_login(usuario)
        resposta = self.client.post('/usuarios/perfil/editar/', {
            'first_name': 'Nome Que Nao Foi Salvo', 'lattes': 'https://site-falso.com/',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.wsgi_request.user.first_name, usuario.first_name)
        usuario.refresh_from_db()
        self.assertNotEqual(usuario.first_name, 'Nome Que Nao Foi Salvo')


class CriacaoDeUsuarioTests(TestCase):
    def test_createsuperuser_cria_coordenador_com_matricula(self):
        from io import StringIO

        from django.core.management import call_command

        with patch.dict('os.environ', {'DJANGO_SUPERUSER_PASSWORD': 'Senha-Forte-2026!'}):
            call_command(
                'createsuperuser', interactive=False, username='primeiro_coord',
                matricula='MAT-001', stdout=StringIO(),
            )
        usuario = Usuario.objects.get(username='primeiro_coord')
        self.assertTrue(usuario.is_coordenador)
        self.assertTrue(usuario.is_superuser)
        self.assertEqual(usuario.matricula, 'MAT-001')

    def test_create_user_continua_criando_membro(self):
        self.assertFalse(_criar('membro_comum').is_coordenador)

    def test_admin_pede_matricula_ao_adicionar_usuario(self):
        admin = Usuario.objects.create_superuser('admin_teste', password='x', matricula='MAT-ADM')
        self.client.force_login(admin)
        resposta = self.client.get('/admin/usuarios/usuario/add/')
        self.assertContains(resposta, 'name="matricula"')


class CabecalhosDeSegurancaTests(TestCase):
    def test_paginas_tem_content_security_policy_sem_script_inline(self):
        resposta = self.client.get('/usuarios/login/')
        politica = resposta['Content-Security-Policy']
        script_src = next(p for p in politica.split(';') if p.strip().startswith('script-src'))
        self.assertIn("'self'", script_src)
        self.assertNotIn('unsafe-inline', script_src)
        self.assertIn("frame-ancestors 'none'", politica)

    def test_nenhum_template_usa_handler_inline(self):
        from pathlib import Path

        from django.conf import settings

        templates = [p for p in Path(settings.BASE_DIR).glob('**/templates/**/*.html') if 'venv' not in p.parts]
        self.assertTrue(templates)
        for caminho in templates:
            with self.subTest(template=str(caminho)):
                self.assertNotRegex(caminho.read_text(encoding='utf-8'), r'\son[a-z]+="')
