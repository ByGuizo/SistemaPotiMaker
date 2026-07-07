from django.urls import path

from . import views

app_name = 'projetos'

urlpatterns = [
    path('', views.kanban, name='kanban'),
    path('novo/', views.novo_projeto, name='novo_projeto'),
    path('<int:pk>/editar/', views.editar_projeto, name='editar_projeto'),
    path('<int:pk>/excluir/', views.excluir_projeto, name='excluir_projeto'),
    path('<int:pk>/mover/<str:direcao>/', views.mover_projeto, name='mover_projeto'),
]
