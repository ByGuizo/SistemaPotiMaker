from django.contrib import admin

from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data', 'hora_inicio', 'local')
    list_filter = ('data',)
    search_fields = ('titulo',)
