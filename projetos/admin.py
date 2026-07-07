from django.contrib import admin

from .models import Projeto


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'prioridade', 'prazo')
    list_filter = ('status', 'prioridade')
    search_fields = ('nome',)
