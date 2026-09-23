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
        """Usuário pendente tem is_active=False, então o backend o rejeita antes de
        confirm_login_allowed(). Aqui damos o motivo real em vez de 'senha incorreta'."""
        usuario = Usuario.objects.filter(username__iexact=self.cleaned_data.get('username', '')).first()
        if usuario and usuario.is_pendente and usuario.check_password(self.cleaned_data.get('password', '')):
            return forms.ValidationError(self.error_messages['pendente'], code='pendente')
        return super().get_invalid_login_error()


class UsernameUnicoMixin:
    """
    Recusa um nome de usuário que já exista com outra combinação de maiúsculas
    ("Guizo" x "guizo"). O unique do banco diferencia maiúsculas; sem isto,
    daria para criar duas contas que parecem a mesma pessoa.
    """

    def clean_username(self):
        username = self.cleaned_data['username']
        existe = Usuario.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError(
                'Já existe um usuário com esse nome (maiúsculas e minúsculas não fazem diferença).'
            )
        return username


class CadastroForm(EstiloPotiMakerMixin, UsernameUnicoMixin, forms.ModelForm):
    """Auto-cadastro público — o usuário nasce pendente de aprovação."""

    # Honeypot ("pote de mel"): campo escondido por CSS que pessoas não veem e
    # robôs de spam preenchem. Se vier preenchido, a view descarta o cadastro.
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


class MembroForm(EstiloPotiMakerMixin, UsernameUnicoMixin, forms.ModelForm):
    """Edição de membro já existente pelo coordenador (não cria novos)."""

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
        # editor = o coordenador logado que está fazendo a edição
        super().__init__(*args, **kwargs)
        self.editor = editor

    def clean_password(self):
        senha = self.cleaned_data.get('password')
        if senha:
            # Mesmas regras do auto-cadastro (tamanho mínimo, senhas comuns...)
            validate_password(senha, user=self.instance)
        return senha

    def clean(self):
        dados = super().clean()
        # self.instance ainda tem os valores do banco: construct_instance só
        # roda depois do clean()
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
