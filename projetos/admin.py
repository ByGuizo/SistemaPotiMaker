from django.contrib import admin

from .models import Atividade, Projeto


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'em_andamento')
    search_fields = ('nome',)


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'projeto', 'status', 'prioridade', 'prazo')
    list_filter = ('status', 'prioridade', 'projeto')
    search_fields = ('nome',)
