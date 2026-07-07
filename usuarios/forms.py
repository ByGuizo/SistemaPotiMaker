from django import forms
from django.contrib.auth.forms import AuthenticationForm

from core.forms import EstiloPotiMakerMixin

from .models import Usuario


class LoginForm(EstiloPotiMakerMixin, AuthenticationForm):
    pass


class MembroForm(EstiloPotiMakerMixin, forms.ModelForm):
    password = forms.CharField(
        label='Senha', widget=forms.PasswordInput, required=False,
        help_text='Deixe em branco para manter a senha atual (ao editar).'
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'username', 'email', 'matricula', 'tipo', 'is_active']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Usuário',
            'email': 'E-mail',
            'is_active': 'Ativo',
        }

    def save(self, commit=True):
        usuario = super().save(commit=False)
        senha = self.cleaned_data.get('password')
        if senha:
            usuario.set_password(senha)
        elif not usuario.pk:
            usuario.set_unusable_password()
        if commit:
            usuario.save()
        return usuario
