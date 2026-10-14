from urllib.parse import urlsplit

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from core.forms import EstiloPotiMakerMixin, SubstituiArquivoMixin

from .models import Usuario


class LoginForm(EstiloPotiMakerMixin, AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'pendente': 'Seu cadastro ainda está aguardando a aprovação de um coordenador.',
    }

    def get_invalid_login_error(self):
        usuario = Usuario.objects.filter(username__iexact=self.cleaned_data.get('username', '')).first()
        if usuario and usuario.is_pendente and usuario.check_password(self.cleaned_data.get('password', '')):
            return forms.ValidationError(self.error_messages['pendente'], code='pendente')
        return super().get_invalid_login_error()


class UsernameUnicoMixin:
    def clean_username(self):
        username = self.cleaned_data['username']
        existe = Usuario.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError(
                'Já existe um usuário com esse nome (maiúsculas e minúsculas não fazem diferença).'
            )
        return username


class CadastroForm(EstiloPotiMakerMixin, UsernameUnicoMixin, forms.ModelForm):
    CAMPO_ARMADILHA = 'website'

    password = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password_confirmacao = forms.CharField(label='Confirme a senha', widget=forms.PasswordInput)
    website = forms.CharField(
        label='Deixe este campo em branco', required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'tabindex': '-1'}),
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'username', 'matricula']
        labels = {
            'first_name': 'Nome completo',
            'username': 'Usuário',
        }

    def clean_password(self):
        senha = self.cleaned_data['password']
        validate_password(senha)
        return senha

    def clean(self):
        dados = super().clean()
        senha = dados.get('password')
        confirmacao = dados.get('password_confirmacao')
        if senha and confirmacao and senha != confirmacao:
            self.add_error('password_confirmacao', 'As senhas não conferem.')
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['password'])
        usuario.tipo = Usuario.Tipo.MEMBRO
        usuario.status_cadastro = Usuario.StatusCadastro.PENDENTE
        usuario.is_active = False
        if commit:
            usuario.save()
        return usuario


class PerfilForm(EstiloPotiMakerMixin, SubstituiArquivoMixin, forms.ModelForm):
    TAMANHO_MAX_MB = 3

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'foto', 'biografia', 'lattes']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'foto': 'Foto de perfil',
            'biografia': 'Biografia',
            'lattes': 'Currículo Lattes',
        }
        help_texts = {
            'foto': 'JPG, PNG ou WEBP de até 3 MB.',
            'biografia': 'Conte um pouco sobre você — no máximo 500 caracteres.',
            'lattes': 'Cole o endereço do seu currículo (ex.: http://lattes.cnpq.br/1234567890123456).',
        }
        widgets = {
            'biografia': forms.Textarea(attrs={'rows': 4, 'maxlength': 500}),
            'lattes': forms.URLInput(attrs={'placeholder': 'http://lattes.cnpq.br/...'}),
        }

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if foto and hasattr(foto, 'content_type'):
            if foto.size > self.TAMANHO_MAX_MB * 1024 * 1024:
                raise forms.ValidationError(
                    f'A imagem deve ter no máximo {self.TAMANHO_MAX_MB} MB '
                    f'(a sua tem {foto.size / 1024 / 1024:.1f} MB).'
                )
            if foto.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
                raise forms.ValidationError('Use uma imagem JPG, PNG ou WEBP.')
        return foto

    def clean_lattes(self):
        url = (self.cleaned_data.get('lattes') or '').strip()
        if not url:
            return url
        endereco = urlsplit(url)
        dominio = (endereco.hostname or '').lower()
        if endereco.scheme not in ('http', 'https') or not (
            dominio == 'lattes.cnpq.br' or dominio.endswith('.lattes.cnpq.br')
        ):
            raise forms.ValidationError(
                'Informe um endereço do Lattes (ex.: http://lattes.cnpq.br/1234567890123456).'
            )
        return url


class MembroForm(EstiloPotiMakerMixin, UsernameUnicoMixin, forms.ModelForm):
    password = forms.CharField(
        label='Senha', widget=forms.PasswordInput, required=False,
        help_text='Deixe em branco para manter a senha atual.'
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'username', 'matricula', 'tipo', 'is_active']
        labels = {
            'first_name': 'Nome completo',
            'username': 'Usuário',
            'is_active': 'Ativo',
        }

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor

    def clean_password(self):
        senha = self.cleaned_data.get('password')
        if senha:
            validate_password(senha, user=self.instance)
        return senha

    def clean(self):
        dados = super().clean()
        membro = self.instance
        desativando = 'is_active' in dados and not dados['is_active']
        rebaixando = dados.get('tipo') and dados['tipo'] != Usuario.Tipo.COORDENADOR

        if self.editor and membro.pk == self.editor.pk and desativando:
            self.add_error('is_active', 'Você não pode desativar a sua própria conta.')
        elif membro.e_ultimo_coordenador_ativo():
            mensagem = (
                'Este é o último coordenador ativo. Promova outro membro a coordenador '
                'antes, senão ninguém mais consegue administrar o sistema.'
            )
            if desativando:
                self.add_error('is_active', mensagem)
            if rebaixando:
                self.add_error('tipo', mensagem)
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        senha = self.cleaned_data.get('password')
        if senha:
            usuario.set_password(senha)
        if commit:
            usuario.save()
        return usuario
