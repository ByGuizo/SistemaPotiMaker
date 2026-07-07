from django.urls import path

from . import views

app_name = 'agenda'

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('novo/', views.novo_evento, name='novo_evento'),
    path('<int:pk>/editar/', views.editar_evento, name='editar_evento'),
    path('<int:pk>/excluir/', views.excluir_evento, name='excluir_evento'),
    path('dia/<int:ano>/<int:mes>/<int:dia>/', views.painel_dia, name='painel_dia'),
]
