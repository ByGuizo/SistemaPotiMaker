from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from core.views import servir_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('inventario/', include('inventario.urls')),
    path('projetos/', include('projetos.urls')),
    path('agenda/', include('agenda.urls')),
    path(f"{settings.MEDIA_URL.strip('/')}/<path:caminho>", servir_media, name='servir_media'),
]
