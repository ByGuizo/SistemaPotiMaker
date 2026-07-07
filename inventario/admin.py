from django.contrib import admin

from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'quantidade', 'status')
    list_filter = ('categoria', 'status')
    search_fields = ('nome',)
