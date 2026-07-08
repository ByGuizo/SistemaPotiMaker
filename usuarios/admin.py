from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import HorarioEscala, RegistroPresenca, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('PotiMaker', {'fields': ('matricula', 'tipo', 'criado_por')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'tipo', 'is_active')
    list_filter = UserAdmin.list_filter + ('tipo',)


@admin.register(RegistroPresenca)
class RegistroPresencaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'data_hora')
    date_hierarchy = 'data_hora'


@admin.register(HorarioEscala)
class HorarioEscalaAdmin(admin.ModelAdmin):
    list_display = ('dia_semana', 'slot')
    list_filter = ('dia_semana', 'slot')
    filter_horizontal = ('membros',)
