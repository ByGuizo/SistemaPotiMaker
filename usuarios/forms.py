from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from core.forms import EstiloPotiMakerMixin

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


class CadastroForm(EstiloPotiMakerMixin, forms.ModelForm):
    """Auto-cadastro público — o usuário nasce pendente de aprovação."""

    password = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password_confirmacao = forms.CharField(label='Confirme a senha', widget=forms.PasswordInput)

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


class MembroForm(EstiloPotiMakerMixin, forms.ModelForm):
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

    def save(self, commit=True):
        usuario = super().save(commit=False)
        senha = self.cleaned_data.get('password')
        if senha:
            usuario.set_password(senha)
        if commit:
            usuario.save()
        return usuario
